package org.matsim.kutno;

import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.prep.PreparedGeometry;
import org.locationtech.jts.geom.prep.PreparedGeometryFactory;
import org.locationtech.jts.io.WKTReader;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.Node;
import org.matsim.contrib.osm.networkReader.SupersonicOsmNetworkReader;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.algorithms.NetworkCleaner;
import org.matsim.core.utils.geometry.transformations.TransformationFactory;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;
import java.util.Set;

/**
 * F2: OSM PBF -> sieć MATSim (car) w EPSG:2180, przycięta do obszaru z make_area.py.
 * Użycie: java -cp <jar> org.matsim.kutno.CreateKutnoNetwork <osm.pbf> <area.wkt> <towns.wkt> <network.properties> <network.xml.gz>
 * Transformacja WGS84 -> EPSG:2180 dzieje się tylko tutaj (parser Supersonic, przed filtrem obszaru).
 * Prędkości (D13): tag maxspeed > limit ustawowy wg typu drogi i położenia (miasto/poza) ; freespeed = limit x factor.
 * Zawrotki na granicy: ślepe końce jezdni jednokierunkowych (np. A1) łączone przed NetworkCleaner (inaczej giną).
 */
public final class CreateKutnoNetwork {

	private static final GeometryFactory GF = new GeometryFactory();

	public static void main(String[] args) throws Exception {
		PreparedGeometry area = readWkt(args[1]);
		PreparedGeometry towns = readWkt(args[2]);
		Properties speeds = new Properties();
		try (Reader r = Files.newBufferedReader(Path.of(args[3]))) {
			speeds.load(r);
		}
		double factor = Double.parseDouble(speeds.getProperty("factor"));

		Network network = new SupersonicOsmNetworkReader.Builder()
				.setCoordinateTransformation(TransformationFactory.getCoordinateTransformation(TransformationFactory.WGS84, "EPSG:2180"))
				.setIncludeLinkAtCoordWithHierarchy((coord, level) -> contains(area, coord))
				.setAfterLinkCreated((link, tags, direction) -> {
					link.setAllowedModes(Set.of(TransportMode.car));
					setSpeed(link, tags, towns, speeds, factor);
				})
				.build()
				.read(args[0]);

		int nodes = network.getNodes().size(), links = network.getLinks().size();
		int turnarounds = addBoundaryTurnarounds(network, speeds, PreparedGeometryFactory.prepare(
				new WKTReader().read(Files.readString(Path.of(args[1]))).buffer(-Double.parseDouble(speeds.getProperty("boundary_zone_m")))));
		new NetworkCleaner().run(network);
		System.out.printf("F2 network: boundary turnarounds added=%d%n", turnarounds);
		System.out.printf("F2 network: before cleaner nodes=%d links=%d, after nodes=%d links=%d%n",
				nodes, links, network.getNodes().size(), network.getLinks().size());
		NetworkUtils.writeNetwork(network, args[4]);
	}

	/** Łączy węzły-ujścia (tylko wjazdy) z najbliższymi węzłami-źródłami (tylko wyjazdy) w strefie granicy sieci. */
	private static int addBoundaryTurnarounds(Network network, Properties p, PreparedGeometry interior) {
		double maxDist = Double.parseDouble(p.getProperty("boundary_turnaround_max_m"));
		double speed = Double.parseDouble(p.getProperty("boundary_turnaround_speed")) / 3.6;
		double capacity = Double.parseDouble(p.getProperty("boundary_turnaround_capacity"));
		// tylko strefa przy granicy: ślepe końce w środku sieci to błędy OSM, nie efekt przycięcia
		var edge = network.getNodes().values().stream().filter(n -> !contains(interior, n.getCoord())).toList();
		var sources = edge.stream().filter(n -> n.getInLinks().isEmpty() && !n.getOutLinks().isEmpty()).toList();
		var sinks = edge.stream().filter(n -> n.getOutLinks().isEmpty() && !n.getInLinks().isEmpty()).toList();
		int added = 0;
		for (Node sink : sinks) {
			Node best = null;
			double bestDist = maxDist;
			for (Node src : sources) {
				double d = NetworkUtils.getEuclideanDistance(sink.getCoord(), src.getCoord());
				if (d <= bestDist) {
					best = src;
					bestDist = d;
				}
			}
			if (best == null) continue;
			Link l = network.getFactory().createLink(Id.createLinkId("turnaround_" + sink.getId() + "_" + best.getId()), sink, best);
			l.setLength(Math.max(bestDist, 10));
			l.setFreespeed(speed);
			l.setCapacity(capacity);
			l.setNumberOfLanes(1);
			l.setAllowedModes(Set.of(TransportMode.car));
			l.getAttributes().putAttribute(NetworkUtils.TYPE, "boundary_turnaround");
			l.getAttributes().putAttribute("speed_source", "boundary_turnaround");
			network.addLink(l);
			added++;
		}
		System.out.printf("F2 network: sinks=%d sources=%d%n", sinks.size(), sources.size());
		return added;
	}

	private static void setSpeed(Link link, Map<String, String> tags, PreparedGeometry towns, Properties speeds, double factor) {
		String highway = tags.get("highway").replace("_link", "");
		Double kmh = parseMaxspeed(tags.get("maxspeed"), speeds);
		String source = "tag";
		if (kmh == null) {
			Coord mid = new Coord((link.getFromNode().getCoord().getX() + link.getToNode().getCoord().getX()) / 2,
					(link.getFromNode().getCoord().getY() + link.getToNode().getCoord().getY()) / 2);
			if (speeds.containsKey(highway)) {
				kmh = Double.parseDouble(speeds.getProperty(highway));
				source = "default_" + highway;
			} else if (contains(towns, mid)) {
				kmh = Double.parseDouble(speeds.getProperty("urban"));
				source = "default_urban";
			} else {
				kmh = Double.parseDouble(speeds.getProperty("rural"));
				source = "default_rural";
			}
		}
		link.setFreespeed(kmh * factor / 3.6);
		link.getAttributes().putAttribute(NetworkUtils.ALLOWED_SPEED, kmh / 3.6);
		link.getAttributes().putAttribute("speed_source", source);
	}

	/** Liczba km/h, "N mph" albo kod "PL:..." z pliku properties; null gdy brak lub nieczytelne (np. "none", "signals"). */
	static Double parseMaxspeed(String tag, Properties speeds) {
		if (tag == null) return null;
		String t = tag.split(";")[0].trim();
		if (speeds.containsKey(t)) return Double.parseDouble(speeds.getProperty(t));
		try {
			if (t.endsWith("mph")) return Double.parseDouble(t.replace("mph", "").trim()) * 1.609;
			return Double.parseDouble(t);
		} catch (NumberFormatException e) {
			return null;
		}
	}

	private static boolean contains(PreparedGeometry g, Coord c) {
		return g.contains(GF.createPoint(new Coordinate(c.getX(), c.getY())));
	}

	private static PreparedGeometry readWkt(String path) throws Exception {
		return PreparedGeometryFactory.prepare(new WKTReader().read(Files.readString(Path.of(path))));
	}
}

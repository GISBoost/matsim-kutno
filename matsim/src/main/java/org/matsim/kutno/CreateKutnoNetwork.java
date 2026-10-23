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
import de.topobyte.osm4j.core.model.iface.EntityContainer;
import de.topobyte.osm4j.core.model.iface.EntityType;
import de.topobyte.osm4j.core.model.iface.OsmRelation;
import de.topobyte.osm4j.core.model.util.OsmModelUtil;
import de.topobyte.osm4j.pbf.seq.PbfIterator;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.turnRestrictions.DisallowedNextLinks;
import org.matsim.core.network.turnRestrictions.DisallowedNextLinksUtils;
import org.matsim.core.network.turnRestrictions.TurnRestrictionsNetworkCleaner;
import org.matsim.core.network.algorithms.NetworkCleaner;
import org.matsim.core.utils.geometry.transformations.TransformationFactory;

import java.io.InputStream;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.Properties;
import java.util.Set;

/**
 * F2: OSM PBF -> sieć MATSim (car) w EPSG:2180, przycięta do obszaru z make_area.py.
 * Użycie: java -cp <jar> org.matsim.kutno.CreateKutnoNetwork <osm.pbf> <area.wkt> <towns.wkt> <network.properties> <network.xml.gz>
 * Transformacja WGS84 -> EPSG:2180 dzieje się tylko tutaj (parser Supersonic, przed filtrem obszaru).
 * Prędkości (D13, D23): tag maxspeed > limit ustawowy wg typu drogi i położenia (miasto/poza); freespeed = limit x factor.<grupa> (D23), a bez grupy x factor.
 * Zakazy skrętu (D26): relacje OSM type=restriction (from way, via node, to way) -> DisallowedNextLinks trybu car; Supersonic ich nie czyta.
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
		applyTurnRestrictions(network, args[0], args[4].replace(".xml.gz", "_zakazy.csv"));
		NetworkUtils.writeNetwork(network, args[4]);
	}

	/**
	 * D26: zakazy skrętu z relacji OSM. Węzły sieci mają id węzłów OSM, link.origid = id drogi (Supersonic).
	 * no_* -> zakazana para (link drogi from kończący się w via, link drogi to zaczynający się w via);
	 * only_* -> zakazane wszystkie inne wyjazdy z via dla linku drogi from. Odrzucane (z licznikiem): via-way, inne rodzaje (no_entry, no_exit),
	 * wyjątki dla samochodów (except), relacje bez linków w sieci. Po zakazach TurnRestrictionsNetworkCleaner (silna spójność z zakazami).
	 */
	private static void applyTurnRestrictions(Network network, String pbf, String csvOut) throws Exception {
		Map<String, Integer> rej = new TreeMap<>();
		List<String[]> rels = new ArrayList<>(); // id, kind, from, via, to
		int total = 0;
		try (InputStream in = Files.newInputStream(Path.of(pbf))) {
			PbfIterator it = new PbfIterator(in, false);
			while (it.hasNext()) {
				EntityContainer c = it.next();
				if (c.getType() != EntityType.Relation) continue;
				OsmRelation r = (OsmRelation) c.getEntity();
				Map<String, String> tags = OsmModelUtil.getTagsAsMap(r);
				if (!"restriction".equals(tags.get("type"))) continue;
				total++;
				String kind = tags.get("restriction") != null ? tags.get("restriction") : tags.get("restriction:motorcar");
				if (kind == null) { rej.merge("brak rodzaju dla samochodu (np. restriction:hgv)", 1, Integer::sum); continue; }
				String ex = tags.getOrDefault("except", "");
				if (ex.contains("motorcar") || ex.contains("motor_vehicle") || ex.contains("vehicle")) { rej.merge("wyjątek except dla samochodów", 1, Integer::sum); continue; }
				String from = null, via = null, to = null;
				int nVia = 0;
				boolean viaWay = false;
				for (int i = 0; i < r.getNumberOfMembers(); i++) {
					var m = r.getMember(i);
					switch (m.getRole()) {
						case "from" -> { if (from == null && m.getType() == EntityType.Way) from = Long.toString(m.getId()); }
						case "to" -> { if (to == null && m.getType() == EntityType.Way) to = Long.toString(m.getId()); }
						case "via" -> { nVia++; if (m.getType() == EntityType.Node) via = Long.toString(m.getId()); else viaWay = true; }
						default -> { }
					}
				}
				if (viaWay) { rej.merge("via = droga (via-way)", 1, Integer::sum); continue; }
				if (nVia != 1 || from == null || to == null) { rej.merge("niekompletna relacja (from/via/to)", 1, Integer::sum); continue; }
				if (!kind.startsWith("no_") && !kind.startsWith("only_")) { rej.merge("rodzaj nieobsługiwany: " + kind, 1, Integer::sum); continue; }
				if (!network.getNodes().containsKey(Id.createNodeId(via))) { rej.merge("via poza siecią (obszar lub węzeł usunięty)", 1, Integer::sum); continue; }
				rels.add(new String[]{Long.toString(r.getId()), kind, from, via, to});
			}
		}
		Map<String, List<Link>> endsAt = new HashMap<>(), startsAt = new HashMap<>();
		for (Link l : network.getLinks().values()) {
			Object o = l.getAttributes().getAttribute("origid");
			if (o == null) continue;
			endsAt.computeIfAbsent(o + "|" + l.getToNode().getId(), k -> new ArrayList<>()).add(l);
			startsAt.computeIfAbsent(o + "|" + l.getFromNode().getId(), k -> new ArrayList<>()).add(l);
		}
		Map<Id<Link>, DisallowedNextLinks> dnl = new HashMap<>();
		List<String> csv = new ArrayList<>();
		csv.add("relation;kind;from_way;via_node;to_way;link_in;link_out");
		int mapped = 0, pairs = 0;
		for (String[] r : rels) {
			List<Link> ins = endsAt.getOrDefault(r[2] + "|" + r[3], List.of());
			List<Link> tos = startsAt.getOrDefault(r[4] + "|" + r[3], List.of());
			if (ins.isEmpty() || tos.isEmpty()) { rej.merge("brak linku from lub to w sieci (droga poza obszarem, usunięta przez cleaner, car-only)", 1, Integer::sum); continue; }
			List<Link> bad = new ArrayList<>();
			if (r[1].startsWith("no_")) bad.addAll(tos);
			else for (Link o : network.getNodes().get(Id.createNodeId(r[3])).getOutLinks().values()) if (!tos.contains(o)) bad.add(o);
			if (bad.isEmpty()) { rej.merge("only_* bez innych wyjazdów (zakaz pusty)", 1, Integer::sum); continue; }
			mapped++;
			for (Link a : ins) for (Link b : bad) {
				dnl.computeIfAbsent(a.getId(), k -> new DisallowedNextLinks()).addDisallowedLinkSequence(TransportMode.car, List.of(b.getId()));
				csv.add(String.join(";", r[0], r[1], r[2], r[3], r[4], a.getId().toString(), b.getId().toString()));
				pairs++;
			}
		}
		dnl.forEach((id, d) -> NetworkUtils.setDisallowedNextLinks(network.getLinks().get(id), d));
		int linksBefore = network.getLinks().size(), nodesBefore = network.getNodes().size();
		new TurnRestrictionsNetworkCleaner().run(network, TransportMode.car);
		DisallowedNextLinksUtils.clean(network);
		if (!DisallowedNextLinksUtils.isValid(network)) throw new IllegalStateException("DisallowedNextLinks niespójne po cleanerze");
		long withDnl = network.getLinks().values().stream().filter(l -> NetworkUtils.getDisallowedNextLinks(l) != null && !NetworkUtils.getDisallowedNextLinks(l).isEmpty()).count();
		Files.write(Path.of(csvOut), csv);
		System.out.printf("G1 zakazy: relacji restriction w PBF=%d, przeniesionych=%d (par linków=%d), linków z DisallowedNextLinks po cleanerze=%d%n", total, mapped, pairs, withDnl);
		rej.forEach((k, v) -> System.out.printf("G1 zakazy: odrzucone %d: %s%n", v, k));
		System.out.printf("G1 zakazy: TurnRestrictionsNetworkCleaner nodes %d -> %d, links %d -> %d%n", nodesBefore, network.getNodes().size(), linksBefore, network.getLinks().size());
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
		String group = speedGroup(highway, contains(towns, midOf(link)));
		double f = speeds.containsKey("factor." + group) ? Double.parseDouble(speeds.getProperty("factor." + group)) : factor;
		link.setFreespeed(kmh * f / 3.6);
		link.getAttributes().putAttribute("speed_group", group);
		link.getAttributes().putAttribute(NetworkUtils.ALLOWED_SPEED, kmh / 3.6);
		link.getAttributes().putAttribute("speed_source", source);
	}

	private static Coord midOf(Link link) {
		return new Coord((link.getFromNode().getCoord().getX() + link.getToNode().getCoord().getX()) / 2,
				(link.getFromNode().getCoord().getY() + link.getToNode().getCoord().getY()) / 2);
	}

	/** Grupa D23 (jak speed_groups() w pipeline/traffic_providers.py): typ OSM bez _link i położenie środka linku (miasto = towns.wkt). */
	static String speedGroup(String hw, boolean urban) {
		if (hw.equals("motorway")) return "A";
		if (!urban && Set.of("trunk", "primary", "secondary").contains(hw)) return "B";
		if (!urban && Set.of("tertiary", "unclassified").contains(hw)) return "C";
		if (!urban && Set.of("residential", "living_street").contains(hw)) return "D";
		if (urban && Set.of("trunk", "primary", "secondary", "tertiary").contains(hw)) return "E";
		if (urban && Set.of("residential", "unclassified", "living_street").contains(hw)) return "F";
		return "inne";
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

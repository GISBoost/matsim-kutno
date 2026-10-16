package org.matsim.kutno;

import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.prep.PreparedGeometry;
import org.locationtech.jts.geom.prep.PreparedGeometryFactory;
import org.locationtech.jts.io.WKTReader;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Network;
import org.matsim.contrib.osm.networkReader.SupersonicOsmNetworkReader;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.algorithms.NetworkCleaner;
import org.matsim.core.utils.geometry.transformations.TransformationFactory;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;

/**
 * F2: OSM PBF -> sieć MATSim (car) w EPSG:2180, przycięta do obszaru z make_area.py.
 * Użycie: java -cp <jar> org.matsim.kutno.CreateKutnoNetwork <osm.pbf> <area_EPSG2180.wkt> <network.xml.gz>
 * Transformacja WGS84 -> EPSG:2180 dzieje się tylko tutaj (parser Supersonic, przed filtrem obszaru).
 */
public final class CreateKutnoNetwork {

	public static void main(String[] args) throws Exception {
		PreparedGeometry area = PreparedGeometryFactory.prepare(new WKTReader().read(Files.readString(Path.of(args[1]))));
		GeometryFactory gf = new GeometryFactory();

		Network network = new SupersonicOsmNetworkReader.Builder()
				.setCoordinateTransformation(TransformationFactory.getCoordinateTransformation(TransformationFactory.WGS84, "EPSG:2180"))
				.setIncludeLinkAtCoordWithHierarchy((coord, level) -> area.contains(gf.createPoint(new Coordinate(coord.getX(), coord.getY()))))
				.setAfterLinkCreated((link, tags, direction) -> link.setAllowedModes(Set.of(TransportMode.car)))
				.build()
				.read(args[0]);

		int nodes = network.getNodes().size(), links = network.getLinks().size();
		new NetworkCleaner().run(network);
		System.out.printf("F2 network: before cleaner nodes=%d links=%d, after nodes=%d links=%d%n",
				nodes, links, network.getNodes().size(), network.getLinks().size());
		NetworkUtils.writeNetwork(network, args[2]);
	}
}

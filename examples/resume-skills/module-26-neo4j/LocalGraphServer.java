import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Path;
import org.neo4j.configuration.GraphDatabaseSettings;
import org.neo4j.configuration.connectors.BoltConnector;
import org.neo4j.configuration.helpers.SocketAddress;
import org.neo4j.dbms.api.DatabaseManagementService;
import org.neo4j.dbms.api.DatabaseManagementServiceBuilder;

/** Actual embedded Community engine with loopback Bolt and a clean stdin shutdown. */
public class LocalGraphServer {
    public static void main(String[] args) throws Exception {
        Path home = Path.of(args[0]).toAbsolutePath();
        int port = Integer.parseInt(args[1]);
        DatabaseManagementService dbms = new DatabaseManagementServiceBuilder(home)
            .setConfig(GraphDatabaseSettings.auth_enabled, false)
            .setConfig(GraphDatabaseSettings.pagecache_memory, 64L * 1024 * 1024)
            .setConfig(BoltConnector.enabled, true)
            .setConfig(BoltConnector.listen_address, new SocketAddress("127.0.0.1", port))
            .setConfig(BoltConnector.advertised_address, new SocketAddress("127.0.0.1", port))
            .setConfig(BoltConnector.encryption_level, BoltConnector.EncryptionLevel.DISABLED)
            .build();
        try {
            System.out.println("M26_READY " + home);
            System.out.flush();
            new BufferedReader(new InputStreamReader(System.in)).readLine();
        } finally {
            dbms.shutdown();
        }
    }
}

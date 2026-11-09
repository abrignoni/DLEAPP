import java.io.*;
import java.util.*;

/** Writes a known object graph with the JDK's own ObjectOutputStream, as a test fixture for a Python reader. */
public class KdSerialOracle {
    enum Kind { ONE, TWO, THREE }

    static class Holder implements Serializable {
        private static final long serialVersionUID = 1L;
        int count = 7;
        long when = 1288051200000L;
        String label = "kd-holder";
        File file = new File("C:\\kd\\a.txt");
        private void writeObject(ObjectOutputStream s) throws IOException {
            s.defaultWriteObject();
            s.writeInt(42);
            s.writeObject("kd-extra");
        }
    }

    public static void main(String[] args) throws Exception {
        Map<String, Object> root = new HashMap<String, Object>();
        root.put("VERSION", Kind.THREE);
        Map<String, List<Integer>> files = new HashMap<String, List<Integer>>();
        files.put("C:\\kd\\a.txt", new ArrayList<Integer>(Arrays.asList(0, 2)));
        files.put("C:\\kd\\b.txt", Collections.<Integer>emptyList());
        root.put("FILES", files);
        SortedMap<Integer, String> names = new TreeMap<Integer, String>();
        names.put(2, "kd-list");
        root.put("NAMES", names);
        root.put("SET", new HashSet<String>(Arrays.asList("urn:sha1:AAAA")));
        root.put("LONG", Long.valueOf(1288051200000L));
        root.put("HOLDER", new Holder());
        root.put("UNMOD", Collections.unmodifiableList(new ArrayList<String>(Arrays.asList("x", "y"))));
        ObjectOutputStream out = new ObjectOutputStream(new FileOutputStream(args[0]));
        out.writeObject(root);
        out.close();
    }
}

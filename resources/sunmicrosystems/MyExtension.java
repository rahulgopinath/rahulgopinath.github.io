package blue;
import tcl.lang.Interp;
import tcl.lang.Extension;

public class MyExtension extends Extension {
    public void init(Interp interp) {
        interp.createCommand(MyCmd.name, new MyCmd());
    }
}


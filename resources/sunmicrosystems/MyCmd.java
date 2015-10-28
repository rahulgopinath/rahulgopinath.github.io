package blue;
import tcl.lang.*;
import java.io.*;
import java.util.*;

public class MyCmd implements tcl.lang.Command {
    public static String name = "my-cmd";
    public void cmdProc(Interp interp, TclObject argv[]) throws TclException {
        if (argv.length == 1)
            throw new TclException(interp,"Need at least 1 argument");
        TclObject obj =  TclList.newInstance();
        try {
            for (Object o: argv) {
                TclList.append(interp, obj, 
                    TclString.newInstance(o.toString()));
            }
            interp.setResult(obj.toString());
        } catch(Exception e){
            throw new TclException(interp, e.getMessage());
        }
    }
}

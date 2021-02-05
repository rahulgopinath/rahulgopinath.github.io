$(document).ready(function () {
//    var output = $('#edoutput');
//    var outf = function (text) {
//        output.text(output.text() + text);
//    };
//
//    var keymap = {
//        "Ctrl-Enter" : function (editor) {
//            Sk.configure({output: outf,
//                 read: builtinRead,
//                 __future__: Sk.python3});
//            Sk.canvas = "mycanvas";
//            if (editor.getValue().indexOf('turtle') > -1 ) {
//                $('#mycanvas').show()
//            }
//            Sk.pre = "edoutput";
//            (Sk.TurtleGraphics || (Sk.TurtleGraphics = {})).target = 'mycanvas';
//            try {
//                Sk.misceval.asyncToPromise(function() {
//                    return Sk.importMainWithBody("<stdin>",false,editor.getValue(),true);
//                });
//            } catch(e) {
//                outf(e.toString() + "\n")
//            }
//        },
//        "Shift-Enter": function (editor) {
//            Sk.configure({output: outf,
//                read: builtinRead,
//                __future__: Sk.python3});
//            Sk.canvas = "mycanvas";
//            Sk.pre = "edoutput";
//            if (editor.getValue().indexOf('turtle') > -1 ) {
//                $('#mycanvas').show()
//            }
//            try {
//                Sk.misceval.asyncToPromise(function() {
//                    return Sk.importMainWithBody("<stdin>",false,editor.getValue(),true);
//                });
//            } catch(e) {
//                outf(e.toString() + "\n")
//            }
//        }
//    }
//
//
//    var editor = CodeMirror.fromTextArea(document.getElementById('code'), {
//        parserfile: ["parsepython.js"],
//        autofocus: true,
//        theme: "solarized dark",
//        //path: "static/env/codemirror/js/",
//        lineNumbers: true,
//        textWrapping: false,
//        indentUnit: 4,
//        height: "100px",
//        fontSize: "8pt",
//        autoMatchParens: true,
//        extraKeys: keymap,
//        parserConfig: {'pythonVersion': 2, 'strictErrors': true}
//    });
//
//    $("#skulpt_run").click(function (e) { keymap["Ctrl-Enter"](editor)} );
//
//    $("#toggledocs").click(function (e) {
//        $("#quickdocs").toggle();
//    });
//
//    var exampleCode = function (id, text) {
//        $(id).click(function (e) {
//            editor.setValue(text);
//            editor.focus(); // so that F5 works, hmm
//        });
//    };
//
//    exampleCode('#codeexample1', "print(\"Hello, World!\")");
//    $('#clearoutput').click(function (e) {
//        $('#edoutput').text('');
//        $('#mycanvas').hide();
//    });
//
//
function builtinRead(x) {
    if (Sk.builtinFiles === undefined || Sk.builtinFiles["files"][x] === undefined)
        throw "File not found: '" + x + "'";
    return Sk.builtinFiles["files"][x];
}


function runit(prefix, editor) { 
   //var prog = document.getElementById("yourcode" + prefix).value;
   var prog = editor.getValue();
   var mypre = document.getElementById("output" + prefix);

   function outf(text) {
      var mypre = document.getElementById("output" + prefix);
      mypre.innerHTML = mypre.innerHTML + text;
   }
   mypre.innerHTML = '';
   Sk.pre = "output" + prefix;
   Sk.configure({output:outf, read:builtinRead, retainglobals: true, __future__: Sk.python3});
   (Sk.TurtleGraphics || (Sk.TurtleGraphics = {})).target = 'mycanvas' + prefix;
   var myPromise = Sk.misceval.asyncToPromise(function() {
       return Sk.importMainWithBody("<stdin>", false, prog, true);
   });
   myPromise.then(function(mod) {
       console.log('success');
   },
       function(err) {
       console.log(err.toString());
   });
}


var editor1 = CodeMirror.fromTextArea(document.getElementById("yourcode1"), { lineNumbers: true });
var editor2 = CodeMirror.fromTextArea(document.getElementById("yourcode2"), { lineNumbers: true });

function runit1() { runit("1", editor1); }
function runit2() { runit("2", editor2); }


$('#button1').click(function() { runit1(); });
$('#button2').click(function() { runit1(); });

//    editor.focus();
});

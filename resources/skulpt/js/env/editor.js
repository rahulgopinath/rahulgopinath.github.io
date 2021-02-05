$(document).ready(function () {

function builtinRead(x) {
    if (Sk.builtinFiles === undefined || Sk.builtinFiles["files"][x] === undefined)
        throw "File not found: '" + x + "'";
    return Sk.builtinFiles["files"][x];
}

function runit(mypre, mycanvas, editor) {
   var prog = editor.getValue();

   function outf(text) {
      mypre.innerHTML = mypre.innerHTML + text;
   }
   function errf(text) {
      mypre.innerHTML = mypre.innerHTML + "<font color='red'>" + text + "</font>";
   }

   mypre.innerHTML = '';
   Sk.pre = mypre.id
   Sk.configure({output:outf, read:builtinRead, retainglobals: true, __future__: Sk.python3});
   (Sk.TurtleGraphics || (Sk.TurtleGraphics = {})).target = mycanvas.id
   var myPromise = Sk.misceval.asyncToPromise(function() {
       return Sk.importMainWithBody("<stdin>", false, prog, true);
   });
   myPromise.then(function(mod) {
       console.log('success');
       editor.display.wrapper.style.border = '1px solid black'
   },
       function(err) {
       console.log(err.toString());
       errf(err.toString())
       editor.display.wrapper.style.border = '1px solid red'
   });
}

$('[name="python_edit"]').each(function(idx) {
   var editor = CodeMirror.fromTextArea($(this)[0], { lineNumbers: false, lineWrapping: true });
   $(this).data('CodeMirrorInstance', editor);
});

$('[name="python_run"]').click(function() { 
  myform = $(this).closest('[name="python_run_form"]');
  //myeditor = myform.find('[name="python_edit"]').next('.CodeMirror').get(0)
  myeditor = myform.find('[name="python_edit"]').data('CodeMirrorInstance')
  mypre = myform.find('[name="python_output"]').first()
  mycanvas = myform.find('[name="python_canvas"]').first()
  runit(mypre[0], mycanvas[0], myeditor)
  //myeditor.display.wrapper.style.border = '1px solid black'
  // var editor = document.querySelector('.CodeMirror').CodeMirror;
});

$('[name="python_run_all"]').click(function() { 
  $(document).find('[name="python_run_form"]').each(function(myform) {
  myeditor = myform.find('[name="python_edit"]').data('CodeMirrorInstance')
  mypre = myform.find('[name="python_output"]').first()
  mycanvas = myform.find('[name="python_canvas"]').first()
  runit(mypre[0], mycanvas[0], myeditor)
  });
});
//    editor.focus();
});

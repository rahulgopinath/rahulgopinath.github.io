$(document).ready(function () {

function runit(mypre, mycanvas, editor) {
   var pre = '__IODIDE_out = io.StringIO()\nsys.stdout = __IODIDE_out\n'
   var prog_ = editor.getValue();
   var post = "\n__IODIDE_out.getvalue()"
   var prog = pre + prog_ + post

   function escHTML(text) {
      return $('<div/>').text(text).html();
   }

   function outf(text) {
      mypre.innerHTML = mypre.innerHTML + escHTML(text);
   }
   function errf(text) {
      mypre.innerHTML = mypre.innerHTML + "<font color='red'>" + escHTML(text) + "</font>";
   }

   mypre.innerHTML = '';

   pyodide.runPythonAsync(prog)
        .then(output => {
           console.log('success');
           outf(output)
           editor.display.wrapper.style.border = '1px solid black'
        })
        .catch((err) => {
           console.log(err.toString());
           errf(err.toString())
           editor.display.wrapper.style.border = '1px solid red'
        });
}

$('[name="python_edit"]').each(function(idx) {
   var editor = CodeMirror.fromTextArea($(this)[0], { lineNumbers: false, lineWrapping: true });
   $(this).data('CodeMirrorInstance', editor);
});

languagePluginLoader.then(() => { 
  pyodide.loadPackage(['micropip']).then(() => {
    var imports_ = $(document).find('#python_pre_edit')
    var imports_lst = [];
    if (imports_.length > 0) {
        var imports_text = imports_.data('CodeMirrorInstance').getValue().replace(/[\r\n]/g,",");
        pyodide.runPython('micropip.install([' + imports_text + '])');
    }

    console.log('pyodide ready');
    var pre =  '\nimport io, sys\n__IODIDE_console=sys.stdout\n'
    var pre_ = '\ndef _dbg(v): print(v, file=__IODIDE_console)\n'

    pyodide.runPython(pre + pre_)

    $('[name="python_run"]').click(function() { 
      myform = $(this).closest('[name="python_run_form"]');
      myeditor = myform.find('[name="python_edit"]').data('CodeMirrorInstance')
      mypre = myform.find('[name="python_output"]').first()
      mycanvas = myform.find('[name="python_canvas"]').first()
      runit(mypre[0], mycanvas[0], myeditor)
    });

    $('[name="python_run_all"]').click(function() { 
      $(document).find('[name="python_run_form"]').each(function(idx, myform_) {
      myform = $(myform_)
      myeditor = myform.find('[name="python_edit"]').data('CodeMirrorInstance')
      if (typeof myeditor !== 'undefined')  {
          mypre = myform.find('[name="python_output"]').first()
          mycanvas = myform.find('[name="python_canvas"]').first()
          runit(mypre[0], mycanvas[0], myeditor)
      }
      });
    });

    $('[name="python_run_all"]').each(function(idx) {
      $(this)[0].style.border = '1px solid red'
    });

  }); //pyodide

}); //lang plugin

}); //document

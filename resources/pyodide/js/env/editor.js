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
     if (typeof mypre != "undefined") {
        mypre.innerHTML = escHTML(text);
     }
      //mypre.innerHTML = mypre.innerHTML + escHTML(text);
   }
   function errf(text) {
     if (typeof mypre != "undefined") {
        mypre.innerHTML = mypre.innerHTML + "<font color='red'>" + escHTML(text) + "</font>";
     }
   }

   function draw(str) {
      $(mycanvas).empty();
      myimg = document.createElement("div");
      $(mycanvas).append(myimg);
      //$(myimg).attr('src', str);
      display_dot(str, myimg)
   }

   if (typeof mypre != "undefined") {
     mypre.innerHTML = '';
   }

   pyodide.globals.set('__canvas__', draw);

   try {
     output = pyodide.runPython(prog);
     console.log('success');
     outf(output);
     editor.display.wrapper.style.border = '1px solid black';
   } catch (err) {
       console.log(err.toString());
       errf(err.toString());
       editor.display.wrapper.style.border = '1px solid red';
   }
}

$('[name="python_edit"]').each(function(idx) {
   var editor = CodeMirror.fromTextArea($(this)[0], { lineNumbers: false, lineWrapping: true });
   $(this).data('CodeMirrorInstance', editor);
});

loadPyodide({
    indexURL: "/resources/pyodide/full/3.9/",
  // fullStdLib: false
}).then((pyodide) => {
  self.pyodide = pyodide;

  var sys_imports = $(document).find('#python_sys_imports')
  var sys_imports_lst = [
    'micropip',
    'mpmath',
    'sympy',
  ]
  if (sys_imports.length > 0) {
      sys_imports_lst_ = sys_imports.data('CodeMirrorInstance').getValue().trim().replace(/[\r\n]/g,",").trim().split(",");
      sys_imports_lst = sys_imports_lst.concat(sys_imports_lst_);
  }

  pyodide.loadPackage(sys_imports_lst).then(() => {
    var installs_ = $(document).find('#python_pre_edit')
    if (installs_.length > 0) {
        var intalls_text = installs_.data('CodeMirrorInstance').getValue().trim().replace(/[\r\n]/g,'","');
        pyodide.runPython('import micropip\nmicropip.install(["' + intalls_text + '"])');
    }

    console.log('pyodide ready');
    var pre =  '\nimport io, sys\n__IODIDE_console=sys.stdout\n'
    var pre_ = '\ndef _dbg(v): print(v, file=__IODIDE_console)\n'

    pyodide.runPython(pre + pre_)

    $('[name="python_run_form"]').each(function(idx, myform_) {
      run_all = $(myform_).find('[name="python_run_all"]');
      if (!run_all.length) {
          myform = $(myform_);
          mybutton = document.createElement("button");
          mybutton.type = "button";
          mybutton.name = "python_run";
          mybutton.innerText = "Run";
          mypre = myform.find('[name="python_output"]').first()
          mypre.before(mybutton);
          $(mybutton).click(function() {
              myform = $(this).closest('[name="python_run_form"]');
              myeditor = myform.find('[name="python_edit"]').data('CodeMirrorInstance')
              mypre = myform.find('[name="python_output"]').first()
              mypre.empty();
              mycanvas = myform.find('[name="python_canvas"]').first()
              runit(mypre[0], mycanvas[0], myeditor)
          });
      }
    });


    $('[name="python_run_all"]').click(function() { 
      $(document).find('[name="python_run_form"]').each(function(idx, myform_) {
      myform = $(myform_)
      myeditor = myform.find('[name="python_edit"]').data('CodeMirrorInstance')
      if (typeof myeditor !== 'undefined')  {
          if (myform.find('[name="python_edit"]')[0].id != 'python_pre_edit') {
            if (myform.find('[name="python_edit"]')[0].id != 'python_sys_imports') {
            mypre = myform.find('[name="python_output"]').first()
            mycanvas = myform.find('[name="python_canvas"]').first()
            runit(mypre[0], mycanvas[0], myeditor)
            }
          }
      }
      });
    });

    $('[name="python_run_all"]').each(function(idx) {
      $(this)[0].style.border = '1px solid red'
    });

  }); //pyodide

}); //lang plugin

}); //document

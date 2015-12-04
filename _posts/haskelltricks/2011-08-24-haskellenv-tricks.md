---
layout: post
categories : post
tagline: "."
tags : [haskelltricks blog haskell language]
e: Haskell environment tricks
review: done
---

Most *lisp editors* have the ability to select a region of code and execute it
separately. Here is how you can get the same ability using *Vim* as the editor
for *Haskell*. It is especially effective with the *XMonad* window manager.

First install [vim screen
plugin](http://www.vim.org/scripts/script.php?script_id=2711). Next
create the files

`~/.vim/after/ftplugin/haskell.vim`

`~/.vim/after/plugin/lhaskell.vim`

with the below content. You also need to have either *Tmux* or *Screen*
installed. (I use Tmux in the tutorial.)

~~~
if exists("b:myhaskellplugin")
finish
endif
let b:myhaskellplugin = 1
nmap <silent> <leader>. :ScreenShell ghci <cr>
nmap <silent> <leader>< :call ScreenShellSend(':l ' . expand("%:p")) <cr>
nmap <silent> <leader>> :call ScreenShellSend(':reload ') <cr>
nmap <silent> <leader>h :call ScreenShellSend(':hoogle ' . expand("<cWORD>")) <cr>
nmap <silent> <leader>t :call ScreenShellSend(':t ' . expand("<cWORD>")) <cr>
~~~


These goes in *~/.vimrc*

~~~
'' choose your own leader here.
let mapleader = ","
let g:ScreenShellInitialFocus='vim'
vmap <C-c><C-c> :ScreenSend<CR>
nmap <C-c><C-c> vip<C-c><C-c>
vnoremap <C-c><C-t> ""y:call ScreenShellSend(':t <C-R>" ')<CR>
let g:ScreenImpl = 'Tmux'
let g:ScreenShellExternal = 1
let g:ScreenShellTerminal = 'xterm'
~~~

Fire up *vim* and edit any *Haskell* file. If everything went well, You will be
able to start a second terminal with the *ghci* started up by typing " ,. "
where "," is the leader we added in the first line. You can load the
current file by typing ",<"

Highlight a portion of text using the *vim* visual command "v"

* Use *Ctrl-c Ctrl-c* to evaluate the selected region.
* Use *Ctrl-c Ctrl-t* to view the type of the selection.

You can also query the current word under cursor in hoogle by typing ,h

Adding other functionalities is just a matter of editing the `~/.vim/after/ftplugin/l?haskell.vim` file.


---
layout: post
category : blog
tagline: "."
tags : [haskelltricks blog haskell language]
e: Haskell environment tricks
---

Most lisp editors have the ability to select a region of code and execute it separately. Here is how you can get the same ability using Vim as the editor for Haskell. It is especially effective with the Xmonad window manager.

First install vim screen plugin. Next add this file to the path `~/.vim/after/ftplugin/haskell.vim` and `~/.vim/after/plugin/lhaskell.vim`. You also need to have either Tmux or Screen installed. (I use Tmux in the tutorial.)

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


Next add this section to your ~/.vimrc

~~~
' choose your own leader here.
let mapleader = ","
let g:ScreenShellInitialFocus='vim'
vmap <C-c><C-c> :ScreenSend<CR>
nmap <C-c><C-c> vip<C-c><C-c>
vnoremap <C-c><C-t> ""y:call ScreenShellSend(':t <C-R>" ')<CR>
let g:ScreenImpl = 'Tmux'
let g:ScreenShellExternal = 1
let g:ScreenShellTerminal = 'xterm'
~~~

Fire up vim and edit any Haskell file. If everything went well, You will be able to fire up a second terminal with the ghci started up by typing " ,. " where "," is the leader we added in the first line. Next you can load the current file by typing ,<

You can also highlight a portion of text using the vim visual command "v" and type ctrl-c ctrl-c to evaluate it. Typing ctrl-c ctrl-t will return its type instead. You can also query the current word under cursor in hoogle by typing ,h

Adding more functionalities is just a matter of editing the ~/.vim/after/ftplugin/haskell.vim file.

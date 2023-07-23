#!/usr/bin/env python3
RETRIES = 50
MASTERSERVER = ('localhost', 8086)
import tkinter
import socket
import threading
import traceback
def recvall(s, n):
    b = b''
    while len(b) < n:
        b += s.recv(n-len(b))
    return b
def genport():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', 0))
        return s.getsockname()[1]
def getpeerlist(laddr, raddr):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(laddr)
        s.connect(raddr)
        n = recvall(s, 1)[0]
        data = recvall(s, n*6)
        s.shutdown(socket.SHUT_RDWR)
        return [(socket.inet_ntop(socket.AF_INET, data[i*6:i*6+4]), data[i*6+4]<<8 | data[i*6+5]) for i in range(n)]
def ui_peerlist(laddr, raddr):
    s = None
    ls = []
    root = tkinter.Tk()
    root.title(f'{laddr} -> {raddr}')
    lsbox = tkinter.Listbox(root)
    btn1 = tkinter.Button(root, text='Refresh')
    btn2 = tkinter.Button(root, text='Connect')
    def refresh(*args):
        nonlocal ls
        lsbox.delete(0, 'end')
        ls = getpeerlist(laddr, raddr)
        for i,v in enumerate(ls):
            if i < len(ls)-1:
                lsbox.insert('end', repr(v))
            else:
                lsbox.insert('end', repr(v)+' (you)')
    def connect(*args):
        nonlocal s
        sel = lsbox.curselection()
        if len(sel) != 1:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(laddr)
        for i in range(RETRIES):
            try:
                s.connect(ls[sel[0]])
                root.destroy()
                return
            except:
                traceback.print_exc()
        s.close()
        s = None
    lsbox.bind('<Double-Button>', connect)
    lsbox.bind('<Return>', connect)
    lsbox.bind('<F5>', refresh)
    btn1.config(command=refresh)
    btn2.config(command=connect)
    lsbox.pack(fill='both', expand=1)
    btn2.pack(side='right')
    btn1.pack(side='right')
    lsbox.focus_set()
    root.mainloop()
    return s
def ui_chat(s):
    thread = None
    try:
        with s:
            root = tkinter.Tk()
            root.title(f'{s.getsockname()} -> {s.getpeername()}')
            txt = tkinter.Text(root)
            try:
                from idlelib.redirector import WidgetRedirector
                redirector = WidgetRedirector(txt)
                txt.insert = redirector.register('insert', lambda *args, **kw: "break")
                txt.delete = redirector.register('delete', lambda *args, **kw: "break")
                txt.replace = redirector.register('replace', lambda *args, **kw: "break")
            except:
                pass
            e = tkinter.Entry(root)
            btn = tkinter.Button(root, text='Send')
            def recv():
                while True:
                    n = recvall(s, 1)[0]
                    msg = recvall(s, n).decode()
                    txt.insert('end', f'Peer: {msg}\n')
            def send(*args):
                txt.insert('end', f'Me: {e.get()}\n')
                line = e.get().encode()
                e.delete(0, 'end')
                s.sendall(bytes([len(line)])+line)
            e.bind('<Return>', send)
            btn.config(command=send)
            txt.pack(fill='both', expand=1)
            btn.pack(side='right')
            e.pack(fill='both')
            e.focus_set()
            thread = threading.Thread(target=recv)
            thread.daemon = True
            thread.start()
            root.mainloop()
            s.shutdown(socket.SHUT_RDWR)
    finally:
        if thread:
            thread.join(.1)
if __name__ == '__main__':
    ui_chat(ui_peerlist(('', genport()), MASTERSERVER))

import tkinter
import datetime


class ChatWindow:
    window = tkinter.Tk()
    out: tkinter.Text
    inp_lb: tkinter.Label
    inp: tkinter.Entry
    err_lb : tkinter.Label
    btn: tkinter.Button

    def __init__(self):
        self.window.geometry("800x600")
        self.window.config(bg='blue')
        self.out = tkinter.Text(self.window, width=95, height=20)
        self.out.config(state = "disabled")
        self.out.pack(pady=15)
        self.inp_lb = tkinter.Label(self.window, text='Сообщение:', font=('Arial', 15, 'bold'), fg='white', bg='blue')
        self.inp = tkinter.Entry(self.window, width=95)
        self.err_lb = tkinter.Label(self.window, text='', font=('Arial', 15, 'bold'), fg='red', bg='blue')
        self.btn = tkinter.Button(self.window, text='Отправить', font=('Arial', 12))

    def show_input(self):
        self.inp_lb.pack(anchor='w', padx = 15)
        self.inp.pack(pady=5)
        self.btn.pack(anchor='w', padx = 15, pady=5)
        self.err_lb.pack()

    def hide_input(self):
        self.inp_lb.pack_forget()
        self.inp.pack_forget()
        self.btn.pack_forget()
        self.err_lb.pack_forget()

    def output(self, string: str, title:str = '', time: bool = True, end :str = '\n'):
        self.out.config(state = 'normal')
        self.out.insert(tkinter.END,
                        f'{[datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')] if time else ""} {title}\n'
                              f'{string}{end}')
        self.out.config(state = 'disabled')

    def clear_output(self):
        self.out.config(state = 'normal')
        self.out.delete('0.0', tkinter.END)
        self.out.config(state='disabled')

    def clear_input(self):
        self.inp.delete('0', tkinter.END)

    def input(self):
        return self.inp.get()

    def error(self, mess: str):
        self.err_lb.config(text = mess)

    def cancel_error(self):
        self.err_lb.config(text='')




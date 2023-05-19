from random import randint
from abc import ABC, abstractmethod
import time
import concurrent.futures
import asyncio
import sqlite3
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import sv_ttk

#класс для работы с бд
class DataBase:
    def __init__(self):
        self.connection = sqlite3.connect('duels.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, winner TEXT, first TEXT, second TEXT, health_1 INT, health_2 INT)")
        self.connection.commit()
    def add_game(self, type, winner, first, second, health_1, health_2):
        self.cursor.execute(f"INSERT into games(type, winner, first, second, health_1, health_2) VALUES(?,?,?,?,?,?);",
            (type, winner, first, second, health_1, health_2))
        self.connection.commit()
    def get_games(self):
        self.cursor.execute("SELECT type,winner FROM games")
        res = self.cursor.fetchall()
        return res
    def get_by_id(self, id):
        self.cursor.execute(f"SELECT type,first,second,health_1,health_2 FROM games WHERE id = ?;", (id,))
        data = self.cursor.fetchone()
        if data != None:
            type, first, second, health_1, health_2 = data[0],data[1],data[2],data[3],data[4]
            return type, first, second, health_1, health_2
        return data
    def update_by_id(self, id, winner, health_1, health_2):
        self.cursor.execute(f"UPDATE games set winner = ?, health_1 = ?, health_2 = ? where id = ?;", (winner, health_1, health_2, id,))
        self.connection.commit()

#класс-декоратор, который выводит время выполнения функции сложения
def time_of_function(function):
    def wrapped(*args):
        start_time = time.perf_counter_ns()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(function, *args)
            res = future.result()
        print('Function completed successfully, execution time',function.__name__,(time.perf_counter_ns() - start_time)/1000000,'milliseconds')
        return res
    return wrapped
#класс исключения на случай если введено не число
class NotInt(Exception):
    def print(self):
        messagebox.showerror('Error', 'The entered data is incorrect')
#класс-декоратор, проверяющий входящие данные в сеттерах, которые меняют одно значение типа int
def setterHealth(function):
    def wrapped(*args):
        try:
            a = args[1]
            if not isinstance(a,int):
                raise NotInt(a)
        except NotInt as ni:
            ni.print()
        else:
            start_time = time.perf_counter_ns()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(function, *args)
            print('Function completed successfully, execution time', function.__name__, (time.perf_counter_ns() - start_time) / 1000000, 'milliseconds')
    return wrapped
#класс здоровья бойца
class Health:
    def __init__(self, health):
        self.health = health
#абстрактный класс бойца
class Fighter(ABC):
    #инициализация - имя и здоровье, этот метод используют все классы-наследники
    def __init__(self, name = '', health = 100, type = '', agility = 0):
        self.name = name
        #композиция - создается класс здоровья для бойца
        self.health = Health(health)
        #тип бойца
        self.__type = type
        #ловкость бойца
        self.__agility = agility
    # сложение, которое будет переопределено в классах-наследниках
    @abstractmethod
    def __add__(self, znach = 20):
        pass
    # вычитание, которое будет переопределено в классах-наследниках
    @abstractmethod
    def __sub__(self,znach = 20):
        pass
    # метод, возвращающий ловкость
    def getAgility(self):
        return self.__agility
    # метод, возвращающий тип
    def getType(self):
        return self.__type
#класс-миксин
class FighterMixin:
    # метод, возвращающий здоровье
    async def getHealth(self):
        health = self.health.health
        await asyncio.sleep(0)
        return health
    # метод, меняющий здоровье
    @setterHealth
    def setHealth(self,num):
        self.health.health = num
#производный класс Боксера
class Boxer(FighterMixin, Fighter):
    #инициализация с присвоением типа Боксера
    def __init__(self,name = '', health = 100, agility = 15):
        Fighter.__init__(self,name,health,'Boxer',agility)
    # переопределение сложения, которое возращает объект с увеличенным здоровьем
    @time_of_function
    def __add__(self, znach=20):
        return Boxer(self.name, self.health.health + znach)
    # переопределение вычитания, которое возращает объект с уменьшенным здоровьем
    @time_of_function
    def __sub__(self, znach=20):
        return Boxer(self.name, self.health.health - znach)
    #метод, который определяет, уклонился ли боксер
    @time_of_function
    def if_parried(self):
        if randint(1,100) <= self.getAgility():
            print('Boxer dodged the blow')
            return True
        else:
            return False
#производный класс Самбиста
class Sambist(FighterMixin, Fighter):
    # инициализация с присвоением типа Самбиста
    def __init__(self, name='', health=100, agility = 20):
        Fighter.__init__(self, name, health, 'Sambist', agility)
    # переопределение сложения, которое возращает объект с увеличенным здоровьем
    @time_of_function
    def __add__(self, znach=20):
        return Sambist(self.name, self.health.health + znach)
    # переопределение вычитания, которое возращает объект с уменьшенным здоровьем
    @time_of_function
    def __sub__(self, znach=20):
        return Sambist(self.name, self.health.health - znach)
    # метод, который определяет, заблокировал ли удар самбист
    @time_of_function
    def if_parried(self):
        if randint(1, 100) <= self.getAgility():
            print('Sambist blocked the shot')
            return True
        else:
            return False
#поединок
class Duel:
    #если c = 1, то создаются боксеры, если c = 2, то создаются самбисты
    def __init__(self, c, name1, name2):
        self.c = c
        if c == 1:
            self.first = Boxer(name1, 100)
            self.second = Boxer(name2, 100)
        elif c == 2:
            self.first = Sambist(name1, 100)
            self.second = Sambist(name2, 100)
    def kick(self):
        # в цикле генерируется значение, если 1, то атакует первый, если 2, то атакует второй
        # у атакованного здоровье уменьшается на 20, если он не парировал удар
        # если атакованный парировал удар, то здоровье не уменьшается
        ud = randint(1, 2)
        if ud == 1:
            if self.second.if_parried():
                first = asyncio.run(self.first.getHealth())
                second = asyncio.run(self.second.getHealth())
                return 3, self.first.getType(), self.first.name, self.second.name, first, second
            else:
                self.second = self.second.__sub__(20)
                first = asyncio.run(self.first.getHealth())
                second = asyncio.run(self.second.getHealth())
        else:
            if self.first.if_parried():
                first = asyncio.run(self.first.getHealth())
                second = asyncio.run(self.second.getHealth())
                return 4, self.first.getType(), self.first.name, self.second.name, first, second
            else:
                self.first = self.first.__sub__(20)
                first = asyncio.run(self.first.getHealth())
                second = asyncio.run(self.second.getHealth())
        # если здоровье какого-либо бойца равно 0, то цикл заканчивается и выводится победитель
        if first == 0:
            return 0, self.first.getType(), self.second.name, self.first.name, first, second
        elif second == 0:
            return 0, self.first.getType(), self.first.name, self.second.name, first, second
        if ud == 1:
            return 1, self.first.getType(), self.first.name, self.second.name, first, second
        else:
            return 2, self.first.getType(), self.first.name, self.second.name, first, second
class NotChosen(Exception):
    def print(self):
        messagebox.showerror('Error', 'You have not selected a game')

class EndedGame(Exception):
    def print(self):
        messagebox.showerror('Error', 'This game is already over')

class Interface:
    def __init__(self):
        self.d = DataBase()
        self.id = 0
        self.window = Tk()
        self.window.title("Game")
        self.window.resizable(width=False, height=False)
        self.window.geometry(f"+{(self.window.winfo_screenwidth() - 250) // 2}+{(self.window.winfo_screenheight() - 450) // 2}")
        sv_ttk.set_theme("dark")

        image = PhotoImage(file="ufc.png")
        Label(self.window, image=image).grid(column=0, row=0, padx=5, pady=5, columnspan=2)

        btn_new = ttk.Button(self.window, text="New game", command=self.clicked_new)
        btn_new.grid(column = 0, row = 1, padx=10, pady=5)

        btn_continue = ttk.Button(self.window, text="Continue game", command=self.clicked_continue)
        btn_continue.grid(column=1, row=1, padx=10, pady=5)

        res = ttk.Label(self.window, text="Game results:")
        res.grid(column = 0, row = 2, padx=0, pady=5, columnspan=2)

        self.results = ttk.Treeview(self.window, height=8)

        self.yscrollbar = ttk.Scrollbar(self.window, orient='vertical', command=self.results.yview)
        self.results.configure(yscrollcommand=self.yscrollbar.set)

        self.results.grid(column = 0, row = 3, padx=10, pady=5, columnspan=2)
        self.yscrollbar.grid(row=3, column=1, sticky='nse')
        self.yscrollbar.configure(command=self.results.yview)

        self.results['columns'] = ('type', 'winner')
        self.results.column("#0", width=0, stretch=NO)
        self.results.column("type", anchor=CENTER, width=80)
        self.results.column("winner", anchor=CENTER, width=80)
        self.results.heading("#0", text="", anchor=CENTER)
        self.results.heading("type", text="Type", anchor=CENTER)
        self.results.heading("winner", text="Winner", anchor=CENTER)
        self.update()

        btn_exit = ttk.Button(self.window, text="Exit", command=self.window.destroy)
        btn_exit.grid(column=0, row=11, padx=10, pady=5)

        self.window.mainloop()

    def update(self):
        data = self.d.get_games()
        for item in self.results.get_children():
            self.results.delete(item)
        count = 1
        for record in data:
            self.results.insert(parent='', index='end', iid=count, text='', values=(record[0], record[1]))
            count += 1

    def kick(self):
        self.beg.grid_remove()
        self.contin.grid(column=0, row=3, padx=5, pady=5)
        n, type, winner, second, health_1, health_2 = self.duel.kick()
        if n == 0:
            self.contin.grid_remove()
            if int(health_1) == 0:
                if self.duel.first.getType() == 'Boxer':
                    self.Text_label.config(text=self.Labels[6])
                    self.Image_label.config(image=self.Images[1])
                else:
                    self.Text_label.config(text=self.Labels[6])
                    self.Image_label.config(image=self.Images[7])
            else:
                if self.duel.first.getType() == 'Boxer':
                    self.Text_label.config(text=self.Labels[5])
                    self.Image_label.config(image=self.Images[0])
                else:
                    self.Text_label.config(text=self.Labels[5])
                    self.Image_label.config(image=self.Images[6])
            self.update()
        elif n == 1:
            self.Text_label.config(text=self.Labels[1])
            if self.duel.first.getType() == 'Boxer':
                self.Image_label.config(image=self.Images[3])
            else:
                self.Image_label.config(image=self.Images[9])
        elif n == 2:
            self.Text_label.config(text=self.Labels[2])
            if self.duel.first.getType() == 'Boxer':
                self.Image_label.config(image=self.Images[4])
            else:
                self.Image_label.config(image=self.Images[10])
        elif n == 3:
            self.Text_label.config(text=self.Labels[4])
            if self.duel.first.getType() == 'Boxer':
                self.Image_label.config(image=self.Images[5])
            else:
                self.Image_label.config(image=self.Images[11])
        else:
            self.Text_label.config(text=self.Labels[3])
            if self.duel.first.getType() == 'Boxer':
                self.Image_label.config(image=self.Images[5])
            else:
                self.Image_label.config(image=self.Images[11])
    def new_game(self):
        if self.new_selected.get() == 1:
            first_name = self.first.get()
            second_name = self.second.get()
            self.window_newgame.destroy()
            self.duel = Duel(1, first_name, second_name)
        else:
            first_name = self.first.get()
            second_name = self.second.get()
            self.window_newgame.destroy()
            self.duel = Duel(2, first_name, second_name)
        self.window_game = Toplevel(self.window)
        self.window_game.title("New game")
        self.window_game.resizable(width=False, height=False)
        self.window_game.geometry(f"+{(self.window.winfo_screenwidth() - 550) // 2}+{(self.window.winfo_screenheight() - 550) // 2}")
        self.Labels = [
            "Begin the game",
            "First kicked second",
            "Second kicked first",
            "First parried",
            "Second parried",
            "First won",
            "Second won",
        ]
        self.Images = [
            PhotoImage(file="boxer_1_won.png"),
            PhotoImage(file="boxer_2_won.png"),
            PhotoImage(file="boxer_begin.png"),
            PhotoImage(file="boxer_kick_1v2.png"),
            PhotoImage(file="boxer_kick_2v1.png"),
            PhotoImage(file="boxer_parried.png"),
            PhotoImage(file="sambist_1_won.png"),
            PhotoImage(file="sambist_2_won.png"),
            PhotoImage(file="sambist_begin.png"),
            PhotoImage(file="sambist_kick_1v2.png"),
            PhotoImage(file="sambist_kick_2v1.png"),
            PhotoImage(file="sambist_parried.png")
        ]

        self.Image_label = ttk.Label(self.window_game, image=self.Images[0])
        self.Image_label.grid(column=0, row=0, padx=5, pady=5, columnspan=2)
        self.Text_label = ttk.Label(self.window_game, text=self.Labels[0])
        self.Text_label.grid(column=0, row=1, padx=5, pady=5, columnspan=2)
        if self.new_selected.get() == 1:
            self.Image_label.config(image = self.Images[2])
        else:
            self.Image_label.config(image=self.Images[8])

        ttk.Button(self.window_game, text="Exit", command=self.exit_game).grid(column=1, row=3, padx=5, pady=5)

        self.beg = ttk.Button(self.window_game, text="Begin", command=self.kick)
        self.beg.grid(column=0, row=3, padx=5, pady=5)
        self.contin = ttk.Button(self.window_game, text="Next", command=self.kick)

        self.window_game.mainloop()
    def continue_game(self, type, name1, name2, health1, health2):
        self.duel = Duel(type, name1, name2)
        self.duel.first.setHealth(health1)
        self.duel.second.setHealth(health2)
        self.window_game = Toplevel(self.window)
        self.window_game.title("New game")
        self.window_game.resizable(width=False, height=False)
        self.window_game.geometry(f"+{(self.window.winfo_screenwidth() - 550) // 2}+{(self.window.winfo_screenheight() - 550) // 2}")
        self.Labels = [
            "Begin the game",
            "First kicked second",
            "Second kicked first",
            "First parried",
            "Second parried",
            "First won",
            "Second won",
        ]
        self.Images = [
            PhotoImage(file="boxer_1_won.png"),
            PhotoImage(file="boxer_2_won.png"),
            PhotoImage(file="boxer_begin.png"),
            PhotoImage(file="boxer_kick_1v2.png"),
            PhotoImage(file="boxer_kick_2v1.png"),
            PhotoImage(file="boxer_parried.png"),
            PhotoImage(file="sambist_1_won.png"),
            PhotoImage(file="sambist_2_won.png"),
            PhotoImage(file="sambist_begin.png"),
            PhotoImage(file="sambist_kick_1v2.png"),
            PhotoImage(file="sambist_kick_2v1.png"),
            PhotoImage(file="sambist_parried.png")
        ]

        self.Image_label = ttk.Label(self.window_game, image=self.Images[0])
        self.Image_label.grid(column=0, row=0, padx=5, pady=5, columnspan=2)
        self.Text_label = ttk.Label(self.window_game, text=self.Labels[0])
        self.Text_label.grid(column=0, row=1, padx=5, pady=5, columnspan=2)
        if type == 1:
            self.Image_label.config(image = self.Images[2])
        else:
            self.Image_label.config(image=self.Images[8])

        ttk.Button(self.window_game, text="Exit", command=self.exit_game).grid(column=1, row=3, padx=5, pady=5)

        self.beg = ttk.Button(self.window_game, text="Begin", command=self.kick)
        self.beg.grid(column=0, row=3, padx=5, pady=5)
        self.contin = ttk.Button(self.window_game, text="Next", command=self.kick)

        self.window_game.mainloop()
    def exit_game(self):
        f = self.duel.first.health.health
        s = self.duel.second.health.health
        if f != 0 and s != 0:
            if self.id == 0:
                self.d.add_game(self.duel.first.getType(),'-',self.duel.first.name,self.duel.second.name,int(f),int(s))
            else:
                data = self.d.get_by_id(self.id)
                first = data[1]
                second = data[2]
                if f == 0:
                    self.d.update_by_id(self.id,second,f,s)
                elif s == 0:
                    self.d.update_by_id(self.id, first, f, s)
                else:
                    self.d.update_by_id(self.id, '-', f, s)
        else:
            if self.id == 0:
                if f == 0:
                    self.d.add_game(self.duel.first.getType(), self.duel.second.name, self.duel.first.name, self.duel.second.name, f, s)
                else:
                    self.d.add_game(self.duel.first.getType(), self.duel.first.name, self.duel.first.name, self.duel.second.name, f, s)
            else:
                data = self.d.get_by_id(self.id)
                first = data[1]
                second = data[2]
                if f == 0:
                    self.d.update_by_id(self.id,second,f,s)
                elif s == 0:
                    self.d.update_by_id(self.id, first, f, s)
                else:
                    self.d.update_by_id(self.id, '-', f, s)
        self.window_game.destroy()
        self.update()
    def clicked_new(self):
        self.id=0
        self.window_newgame = Toplevel(self.window)
        #window_newgame = Tk()
        self.window_newgame.title("New game")
        self.window_newgame.resizable(width=False, height=False)
        self.window_newgame.geometry(f"+{(self.window.winfo_screenwidth() - 350) // 2}+{(self.window.winfo_screenheight() - 300) // 2}")

        self.new_selected = IntVar(master=self.window_newgame)
        self.new_selected.set(1)
        boxers = ttk.Radiobutton(self.window_newgame, text='Boxers', variable=self.new_selected, value=1)
        sambists = ttk.Radiobutton(self.window_newgame, text='Sambists', variable=self.new_selected, value=2)

        btn_exit = ttk.Button(self.window_newgame, text="Exit", command = self.window_newgame.destroy)
        btn_begin = ttk.Button(self.window_newgame, text="Begin", command = self.new_game)

        first_lbl = ttk.Label(self.window_newgame, text="Name of the first fighter:")
        self.first = ttk.Entry(self.window_newgame, width=20)

        second_lbl = ttk.Label(self.window_newgame, text="Name of the second fighter:")
        self.second = ttk.Entry(self.window_newgame, width=20)

        boxers.grid(column=0, row=0, padx=10, pady=5)
        sambists.grid(column=1, row=0, padx=10, pady=5)
        first_lbl.grid(column=0, row=1, padx=10, pady=5)
        self.first.grid(column=1, row=1, padx=10, pady=5)
        second_lbl.grid(column=0, row=2, padx=10, pady=5)
        self.second.grid(column=1, row=2, padx=10, pady=5)
        btn_exit.grid(column=0, row=3, padx=10, pady=5)
        btn_begin.grid(column=1, row=3, padx=10, pady=5)
        self.window_newgame.mainloop()
    def clicked_continue(self):
        try:
            if self.results.focus() == '':
                raise NotChosen()
        except NotChosen as nc:
            nc.print()
        else:
            try:
                self.id = self.results.focus()
                t, first, second, health_1, health_2 = self.d.get_by_id(self.id)
                if int(health_1) == 0 or int(health_2) == 0:
                    raise EndedGame()
            except EndedGame as ed:
                ed.print()
            else:
                if t == 'Boxer':
                    type = 1
                else:
                    type = 2
                self.continue_game(type, first, second, health_1, health_2)
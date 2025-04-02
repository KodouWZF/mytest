import tkinter as tk
from random import randint
from tkinter import messagebox


class SnakeGame:
    def __init__(self, master):
        self.master = master
        master.title("🐍 贪吃蛇大作战")

        # 游戏配置
        self.canvas_size = 400
        self.cell_size = 20
        self.speed = 150  # 毫秒
        self.direction = "Right"
        self.new_direction = "Right"

        # 初始化元素
        self.canvas = tk.Canvas(master, width=self.canvas_size, height=self.canvas_size, bg="#1a1a1a")
        self.canvas.pack(padx=10, pady=10)

        # 分数显示
        self.score = 0
        self.score_label = tk.Label(master, text=f"分数: {self.score}", font=("Arial", 14), fg="#4CAF50")
        self.score_label.pack()

        # 初始化蛇和食物
        self.snake = [[10, 10], [9, 10], [8, 10]]
        self.food = self.generate_food()

        # 绑定键盘事件
        master.bind("<Key>", self.on_key_press)
        self.draw()
        self.move_snake()

    def draw(self):
        self.canvas.delete("all")
        # 绘制蛇
        for x, y in self.snake:
            self.canvas.create_rectangle(
                x * self.cell_size, y * self.cell_size,
                (x + 1) * self.cell_size, (y + 1) * self.cell_size,
                fill="#4CAF50", outline="#357a38"
            )
        # 绘制食物
        fx, fy = self.food
        self.canvas.create_oval(
            fx * self.cell_size, fy * self.cell_size,
            (fx + 1) * self.cell_size, (fy + 1) * self.cell_size,
            fill="#ff5722", outline="#b71c1c"
        )

    def generate_food(self):
        while True:
            food = [randint(0, 19), randint(0, 19)]
            if food not in self.snake:
                return food

    def check_collision(self):
        head = self.snake[0]
        # 边界碰撞
        if head[0] < 0 or head[0] >= 20 or head[1] < 0 or head[1] >= 20:
            return True
        # 自身碰撞
        if head in self.snake[1:]:
            return True
        return False

    def move_snake(self):
        head = self.snake[0].copy()

        # 方向控制（避免反向移动）
        if (self.new_direction == "Up" and self.direction != "Down" or
                self.new_direction == "Down" and self.direction != "Up" or
                self.new_direction == "Left" and self.direction != "Right" or
                self.new_direction == "Right" and self.direction != "Left"):
            self.direction = self.new_direction

        # 移动逻辑
        if self.direction == "Right": head[0] += 1
        if self.direction == "Left": head[0] -= 1
        if self.direction == "Up": head[1] -= 1
        if self.direction == "Down": head[1] += 1

        self.snake.insert(0, head)

        # 吃食物判定
        if head == self.food:
            self.score += 1
            self.score_label.config(text=f"分数: {self.score}")
            self.food = self.generate_food()
        else:
            self.snake.pop()

        # 碰撞检测
        if self.check_collision():
            messagebox.showinfo("游戏结束", f"最终得分: {self.score}")
            self.master.destroy()
            return

        self.draw()
        self.master.after(self.speed - (self.score // 5) * 10, self.move_snake)  # 加速机制

    def on_key_press(self, event):
        key = event.keysym
        if key in ("Up", "Down", "Left", "Right"):
            self.new_direction = key


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("440x480")
    root.resizable(False, False)
    game = SnakeGame(root)
    root.mainloop()
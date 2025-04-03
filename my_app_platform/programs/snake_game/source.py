import tkinter as tk
import random

def center_window(win):
    """
    将窗口居中显示在屏幕上。
    """
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

class SnakeGame:
    def __init__(self, master):
        self.master = master
        self.master.title("贪吃蛇大作战")
        
        # 设置窗口大小，并调用center_window函数使窗口居中
        self.master.geometry("400x450")
        center_window(self.master)
        self.master.resizable(False, False)
        
        self.canvas = tk.Canvas(self.master, bg="black", width=400, height=400)
        self.canvas.pack()
        
        self.score_label = tk.Label(self.master, text="分数: 0", font=("Arial", 12))
        self.score_label.pack()
        
        # 游戏初始状态
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.snake_size = 10
        self.direction = "Right"
        self.new_direction = "Right"
        self.food = self.create_food()
        self.food_size = 10
        self.score = 0
        self.game_over = False
        
        # 新增：开始屏幕状态
        self.start_screen = True
        
        # 绑定键盘事件
        self.master.bind("<KeyPress>", self.handle_key_press)
        
        self.update()
    
    def create_food(self):
        x = random.randint(1, 39) * 10
        y = random.randint(1, 39) * 10
        return (x, y)
    
    def handle_key_press(self, event):
        if self.start_screen:
            # 如果是开始屏幕，按下任意键进入游戏
            self.start_screen = False
        else:
            # 正常游戏逻辑
            key = event.keysym
            if key == "Up" and self.direction != "Down":
                self.new_direction = "Up"
            elif key == "Down" and self.direction != "Up":
                self.new_direction = "Down"
            elif key == "Left" and self.direction != "Right":
                self.new_direction = "Left"
            elif key == "Right" and self.direction != "Left":
                self.new_direction = "Right"
    
    def move(self):
        head_x, head_y = self.snake[0]
        if self.direction == "Up":
            new_head = (head_x, head_y - 10)
        elif self.direction == "Down":
            new_head = (head_x, head_y + 10)
        elif self.direction == "Left":
            new_head = (head_x - 10, head_y)
        elif self.direction == "Right":
            new_head = (head_x + 10, head_y)
        
        self.snake.insert(0, new_head)
        
        if new_head == self.food:
            self.score += 10
            self.score_label.config(text=f"分数: {self.score}")
            self.food = self.create_food()
        else:
            self.snake.pop()
    
    def check_collision(self):
        head_x, head_y = self.snake[0]
        if head_x < 0 or head_x >= 400 or head_y < 0 or head_y >= 400:
            return True
        if self.snake[0] in self.snake[1:]:
            return True
        return False
    
    def draw(self):
        self.canvas.delete("all")
        
        if self.start_screen:
            # 开始屏幕提示
            self.canvas.create_text(200, 200, text="按任意键开始", fill="white", font=("Arial", 24))
        else:
            # 绘制蛇
            for segment in self.snake:
                x, y = segment
                self.canvas.create_rectangle(x, y, x + self.snake_size, y + self.snake_size, fill="green")
            
            # 绘制食物
            food_x, food_y = self.food
            self.canvas.create_oval(food_x, food_y, food_x + self.food_size, food_y + self.food_size, fill="red")
            
            # 如果游戏结束，显示游戏结束文本
            if self.game_over:
                self.canvas.create_text(200, 200, text="游戏结束", fill="white", font=("Arial", 24))
                self.canvas.create_text(200, 240, text=f"最终分数: {self.score}", fill="white", font=("Arial", 18))
                self.canvas.create_text(200, 280, text="按空格键重新开始", fill="white", font=("Arial", 14))
    
    def reset_game(self):
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.direction = "Right"
        self.new_direction = "Right"
        self.food = self.create_food()
        self.score = 0
        self.score_label.config(text="分数: 0")
        self.game_over = False
        self.start_screen = True  # 重置为开始屏幕状态
    
    def update(self):
        if not self.start_screen and not self.game_over:
            self.direction = self.new_direction
            self.move()
            if self.check_collision():
                self.game_over = True
                self.master.bind("<space>", lambda event: self.reset_game())
        
        self.draw()
        
        speed = max(50, 200 - self.score // 20 * 10)
        self.master.after(speed, self.update)

# 创建主窗口并启动游戏
if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()
/**
 * @fileoverview 前端交互逻辑，处理程序运行、添加和删除。
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');

    // 初始化 CodeMirror 编辑器
    var codeTextarea = document.getElementById('program-code');
    var editor = null;
    if (codeTextarea) {
        editor = CodeMirror.fromTextArea(codeTextarea, {
            lineNumbers: true,
            mode: "python",
            theme: "material-darker", // 匹配引入的 CSS 主题
            indentUnit: 4,
            smartIndent: true,
            tabSize: 4,
            indentWithTabs: false,
            extraKeys: {"Tab": "indentMore", "Shift-Tab": "indentLess"}
        });
        console.log('CodeMirror 编辑器已初始化');
    } else {
        console.error('未找到 program-code 文本区域');
    }

    // ----- 获取页面元素 -----
    var programsContainer = document.getElementById('programs-container');
    var addProgramForm = document.getElementById('add-program-form');
    var deleteProgramsForm = document.getElementById('delete-programs-form');
    var addMessageDiv = document.getElementById('add-message');
    var deleteMessageDiv = document.getElementById('delete-message');
    
    // 菜单相关元素
    var menuButton = document.querySelector('.menu-button');
    var dropdown = document.querySelector('.dropdown');
    
    // 打印关键元素是否存在
    console.log('关键元素检查:', {
        addProgramForm: addProgramForm ? true : false,
        deleteProgramsForm: deleteProgramsForm ? true : false,
        programsContainer: programsContainer ? true : false
    });
    
    // ----- 菜单交互功能 -----
    
    // 点击文件菜单按钮
    if (menuButton && dropdown) {
        menuButton.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.classList.toggle('active');
        });
        
        // 点击文档其他地方关闭菜单
        document.addEventListener('click', function() {
            dropdown.classList.remove('active');
        });
    }
    
    // 添加程序菜单项
    var addBtn = document.getElementById('show-add-form-button');
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            console.log('点击添加程序按钮');
            toggleForms('add');
        });
    }
    
    // 批量删除菜单项
    var deleteBtn = document.getElementById('show-delete-form-button');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            console.log('点击批量删除按钮');
            toggleForms('delete');
        });
    }
    
    // 清理所有程序菜单项
    var cleanAllBtn = document.getElementById('clean-all-programs-button');
    if (cleanAllBtn) {
        cleanAllBtn.addEventListener('click', function() {
            console.log('点击清理所有程序按钮');
            if (confirm('确定要清理所有程序吗？此操作将删除所有程序和相关文件，无法恢复！')) {
                cleanAllPrograms();
            }
        });
    }
    
    // 取消添加按钮
    var cancelAddBtn = document.getElementById('cancel-add-button');
    if (cancelAddBtn) {
        cancelAddBtn.addEventListener('click', function() {
            console.log('点击取消添加按钮');
            hideAllForms();
        });
    }
    
    // 取消删除按钮
    var cancelDeleteBtn = document.getElementById('cancel-delete-button');
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', function() {
            console.log('点击取消删除按钮');
            hideAllForms();
        });
    }
    
    // ----- 程序运行功能 -----
    
    // 程序项点击处理
    function handleProgramClick(event) {
        console.log('程序项被点击', event.target);
        
        var programItem = event.target.closest('.program-item');
        if (!programItem) return;
        
        var programName = programItem.dataset.programName;
        console.log('运行程序:', programName);
        
        if (programItem.getAttribute('data-processing') === 'true') {
            console.log('程序正在处理中');
            return;
        }
        
        programItem.setAttribute('data-processing', 'true');
        programItem.style.opacity = '0.7';
        
        // 发送请求运行程序
        fetch('/run_program', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: programName })
        })
        .then(function(response) { return response.json(); })
        .then(function(result) {
            if (result.status === 'error') {
                alert(result.message);
            } else {
                console.log('程序启动成功');
            }
        })
        .catch(function(error) {
            console.error('运行程序出错:', error);
            alert('运行程序出错: ' + error);
        })
        .finally(function() {
            programItem.style.opacity = '1';
            programItem.removeAttribute('data-processing');
        });
    }
    
    // 绑定程序点击事件
    if (programsContainer) {
        programsContainer.addEventListener('click', handleProgramClick);
    }
    
    // ----- 添加程序功能 -----
    
    // 提交添加程序表单
    if (addProgramForm) {
        addProgramForm.onsubmit = function(event) {
            event.preventDefault();
            console.log('提交添加程序表单');
            
            // 从 CodeMirror 编辑器获取代码
            var programCode = editor ? editor.getValue().trim() : ''; 
            
            var programName = document.getElementById('program-name').value.trim();
            var programIcon = document.getElementById('program-icon');
            var addMessageDiv = document.getElementById('add-message');
            
            if (!programName || !programCode) {
                showMessage(addMessageDiv, '程序名和代码不能为空', 'error');
                return;
            }
            
            if (!/^[a-zA-Z0-9_]+$/.test(programName)) {
                showMessage(addMessageDiv, '程序名只能包含字母、数字和下划线', 'error');
                return;
            }
            
            // 检查常见代码问题 (Python only now)
            if (programCode.indexOf('`') === 0) {
                    showMessage(addMessageDiv, '代码不应以反引号开头，请删除开头的"`"符号', 'error');
                    return;
            }
            
            // 检查代码的第一行是否异常（混入了文件名等）
            var firstLine = programCode.split('\n')[0];
            if (firstLine.includes('.png') || firstLine.includes('.jpg')) {
                    showMessage(addMessageDiv, '代码第一行可能包含文件名，请检查并修正', 'error');
                    return;
            }
            
            var formData = new FormData();
            formData.append('name', programName);
            formData.append('code', programCode);
            formData.append('language', 'python'); // Hardcode language to python
            
            if (programIcon.files.length > 0) {
                formData.append('icon', programIcon.files[0]);
            }
            
            // 显示加载中状态
            showMessage(addMessageDiv, '正在打包程序为EXE，这可能需要一点时间...', 'info');
            
            // 创建一个带超时的fetch（20分钟超时）
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 1200000); // 20分钟超时
            
            // 添加详细的错误处理
            fetch('/add_program', {
                method: 'POST',
                body: formData,
                signal: controller.signal // 关联AbortController
            })
            .then(function(response) { 
                console.log('收到服务器响应:', response.status, response.statusText);
                clearTimeout(timeoutId); // 清除超时
                if (!response.ok) {
                    throw new Error('网络请求失败: ' + response.status + ' ' + response.statusText);
                }
                return response.json(); 
            })
            .then(function(result) {
                console.log('处理服务器返回结果:', result);
                if (result.status === 'success') {
                    // 成功后操作
                    addProgramForm.reset();
                    hideAllForms();
                    alert(result.message);
                    addNewProgram(programName, result.icon_path, 'python');
                } else {
                    // 错误处理
                    showMessage(addMessageDiv, result.message, result.status);
                }
            })
            .catch(function(error) {
                clearTimeout(timeoutId); // 确保清除超时
                console.error('添加程序出错:', error);
                
                let errorMessage = '添加程序出错: ';
                
                // 检查是否是超时错误
                if (error.name === 'AbortError') {
                    errorMessage += '请求超时，程序打包可能需要更长时间。请尝试使用更简单的代码或稍后再试。';
                } else if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
                    errorMessage += '无法连接到服务器，请检查网络连接或服务器是否在运行。';
                } else {
                    errorMessage += error.message || error.toString();
                }
                
                showMessage(addMessageDiv, errorMessage, 'error');
                
                // 尝试获取更多错误信息
                try {
                    var errorDetails = JSON.stringify(error);
                    console.error('错误详情:', errorDetails);
                } catch (e) {
                    console.error('无法序列化错误对象');
                }
            });
        };
    }
    
    // ----- 删除程序功能 -----
    
    // 全选按钮
    var selectAllButton = document.getElementById('select-all-button');
    if (selectAllButton) {
        selectAllButton.onclick = function() {
            console.log('点击全选按钮');
            var checkboxes = document.querySelectorAll('#delete-programs-form input[type="checkbox"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = true;
            });
        };
    }
    
    // 取消全选按钮
    var deselectAllButton = document.getElementById('deselect-all-button');
    if (deselectAllButton) {
        deselectAllButton.onclick = function() {
            console.log('点击取消全选按钮');
            var checkboxes = document.querySelectorAll('#delete-programs-form input[type="checkbox"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = false;
            });
        };
    }
    
    // 提交删除程序表单
    if (deleteProgramsForm) {
        deleteProgramsForm.onsubmit = function(event) {
            event.preventDefault();
            console.log('提交删除程序表单');
            
            var checkboxes = deleteProgramsForm.querySelectorAll('input[type="checkbox"]:checked');
            var selectedPrograms = Array.from(checkboxes).map(function(cb) {
                return cb.value;
            });
            
            if (selectedPrograms.length === 0) {
                alert('请至少选择一个要删除的程序');
                return;
            }
            
            if (!confirm('确定要删除选中的 ' + selectedPrograms.length + ' 个程序吗？此操作不可恢复！')) {
                return;
            }
            
            fetch('/delete_programs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ programs: selectedPrograms })
            })
            .then(function(response) { return response.json(); })
            .then(function(result) {
                if (result.status === 'success' || result.status === 'partial') {
                    // 从页面中移除被删除的程序
                    selectedPrograms.forEach(function(programName) {
                        var item = document.querySelector('.program-item[data-program-name="' + programName + '"]');
                        if (item) item.remove();
                    });
                    
                    hideAllForms();
                    alert(result.message);
                    
                    // 检查是否还有程序，如果没有则隐藏程序网格
                    var container = document.getElementById('programs-container');
                    if (container && container.children.length === 0) {
                        var gridSection = document.getElementById('program-grid');
                        if (gridSection) gridSection.remove();
                    }
                } else {
                    alert(result.message);
                }
            })
            .catch(function(error) {
                console.error('删除程序出错:', error);
                alert('删除程序出错: ' + error);
            });
        };
    }
    
    // ----- 辅助函数 -----
    
    // 显示消息
    function showMessage(element, message, type) {
        element.textContent = message;
        element.className = 'message ' + type;
        element.style.display = 'block';
    }
    
    // 添加新程序到网格
    function addNewProgram(programName, iconPath, programLanguage) {
        var gridSection = document.getElementById('program-grid');
        var container = document.getElementById('programs-container');
        
        // 如果网格不存在，创建新的网格
        if (!gridSection) {
            gridSection = document.createElement('section');
            gridSection.id = 'program-grid';
            
            container = document.createElement('div');
            container.id = 'programs-container';
            container.addEventListener('click', handleProgramClick);
            
            gridSection.appendChild(container);
            
            var mainElement = document.querySelector('main');
            var addSection = document.getElementById('add-program');
            
            if (addSection && mainElement) {
                mainElement.insertBefore(gridSection, addSection);
            } else if (mainElement) {
                mainElement.appendChild(gridSection);
            }
        }
        
        // 创建新的程序项
        var newItem = document.createElement('div');
        newItem.className = 'program-item';
        newItem.setAttribute('data-program-name', programName);
        
        // 添加语言标识，用于在UI中区分不同语言的程序
        if (programLanguage) {
            newItem.setAttribute('data-language', programLanguage);
        }
        
        var iconImg = document.createElement('img');
        iconImg.src = '/static/' + iconPath;
        iconImg.alt = programName + ' 图标';
        iconImg.className = 'program-icon';
        
        var nameSpan = document.createElement('span');
        nameSpan.className = 'program-name';
        nameSpan.textContent = programName;
        
        // 添加语言标签
        if (programLanguage) {
            var languageTag = document.createElement('span');
            languageTag.className = 'language-tag ' + programLanguage;
            languageTag.textContent = programLanguage.toUpperCase();
            newItem.appendChild(languageTag);
        }
        
        newItem.appendChild(iconImg);
        newItem.appendChild(nameSpan);
        container.appendChild(newItem);
    }
    
    // 统一的表单切换函数
    function toggleForms(formType) {
        var addSection = document.getElementById('add-program');
        var deleteSection = document.getElementById('delete-programs');
        
        if (!addSection || !deleteSection) {
            console.error('找不到表单部分');
            return;
        }
        
        // 确保所有表单先隐藏
        addSection.classList.add('hidden');
        deleteSection.classList.add('hidden');
        
        // 然后显示选中的表单
        if (formType === 'add') {
            addSection.classList.remove('hidden');
            console.log('显示添加程序表单');
        } else if (formType === 'delete') {
            deleteSection.classList.remove('hidden');
            console.log('显示批量删除表单');
        }
        
        // 关闭下拉菜单
        var dropdownElem = document.querySelector('.dropdown');
        if (dropdownElem) {
            dropdownElem.classList.remove('active');
        }
    }
    
    // 隐藏所有表单
    function hideAllForms() {
        var addSection = document.getElementById('add-program');
        var deleteSection = document.getElementById('delete-programs');
        
        if (addSection) addSection.classList.add('hidden');
        if (deleteSection) deleteSection.classList.add('hidden');
    }
    
    // 检测键盘快捷键
    document.addEventListener('keydown', function(event) {
        // Ctrl+N: 添加新程序
        if (event.ctrlKey && event.key === 'n') {
            event.preventDefault();
            toggleForms('add');
        }
        
        // Ctrl+D: 批量删除程序
        if (event.ctrlKey && event.key === 'd') {
            event.preventDefault();
            toggleForms('delete');
        }
        
        // Ctrl+C: 清理所有程序
        if (event.ctrlKey && event.key === 'c') {
            event.preventDefault();
            if (confirm('确定要清理所有程序吗？此操作将删除所有程序和相关文件，无法恢复！')) {
                cleanAllPrograms();
            }
        }
    });

    // 清理所有程序函数
    function cleanAllPrograms() {
        fetch('/clean_all_programs', {
            method: 'POST'
        })
        .then(function(response) { return response.json(); })
        .then(function(result) {
            alert(result.message);
            if (result.status === 'success') {
                // 清理成功后刷新页面
                window.location.reload();
            }
        })
        .catch(function(error) {
            console.error('清理程序出错:', error);
            alert('清理程序出错: ' + error);
        });
    }

    // 加载示例代码按钮
    var loadExampleButton = document.getElementById('load-example-button');
    if (loadExampleButton) {
        loadExampleButton.addEventListener('click', function() {
            console.log('点击加载示例代码按钮');
            if (editor) {
                // 贪吃蛇游戏示例代码
                var snakeGameCode = `import tkinter as tk
import random

class SnakeGame:
    def __init__(self, master):
        self.master = master
        self.master.title("贪吃蛇大作战")
        self.master.geometry("400x450")
        self.master.resizable(False, False)
        
        self.canvas = tk.Canvas(self.master, bg="black", width=400, height=400)
        self.canvas.pack()
        
        self.score_label = tk.Label(self.master, text="分数: 0", font=("Arial", 12))
        self.score_label.pack()
        
        # 蛇的初始位置和身体
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.snake_size = 10
        self.direction = "Right"
        self.new_direction = "Right"
        
        # 食物初始位置
        self.food = self.create_food()
        self.food_size = 10
        
        self.score = 0
        self.game_over = False
        
        # 绑定键盘事件
        self.master.bind("<KeyPress>", self.change_direction)
        
        self.update()
    
    def create_food(self):
        # 创建随机位置的食物
        x = random.randint(1, 39) * 10
        y = random.randint(1, 39) * 10
        return (x, y)
    
    def change_direction(self, event):
        # 改变蛇的方向，但防止直接反向移动
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
        # 获取蛇头位置
        head_x, head_y = self.snake[0]
        
        # 根据方向移动蛇头
        if self.direction == "Up":
            new_head = (head_x, head_y - 10)
        elif self.direction == "Down":
            new_head = (head_x, head_y + 10)
        elif self.direction == "Left":
            new_head = (head_x - 10, head_y)
        elif self.direction == "Right":
            new_head = (head_x + 10, head_y)
        
        # 将新头部添加到蛇身体前面
        self.snake.insert(0, new_head)
        
        # 检查是否吃到食物
        if new_head == self.food:
            self.score += 10
            self.score_label.config(text=f"分数: {self.score}")
            self.food = self.create_food()
        else:
            # 如果没吃到食物，移除尾部（保持长度）
            self.snake.pop()
    
    def check_collision(self):
        # 获取蛇头位置
        head_x, head_y = self.snake[0]
        
        # 检查是否撞墙
        if head_x < 0 or head_x >= 400 or head_y < 0 or head_y >= 400:
            return True
        
        # 检查是否撞到自己的身体
        if self.snake[0] in self.snake[1:]:
            return True
        
        return False
    
    def draw(self):
        # 清空画布
        self.canvas.delete("all")
        
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
        # 重置游戏状态
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.direction = "Right"
        self.new_direction = "Right"
        self.food = self.create_food()
        self.score = 0
        self.score_label.config(text="分数: 0")
        self.game_over = False
    
    def update(self):
        if not self.game_over:
            # 更新方向
            self.direction = self.new_direction
            
            # 移动蛇
            self.move()
            
            # 检查碰撞
            if self.check_collision():
                self.game_over = True
                
                # 绑定空格键重新开始
                self.master.bind("<space>", lambda event: self.reset_game())
        
        # 绘制游戏
        self.draw()
        
        # 更新速度，分数越高越快
        speed = max(50, 200 - self.score // 20 * 10)
        
        # 继续游戏循环
        self.master.after(speed, self.update)

# 创建主窗口并启动游戏
if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()`;
                
                editor.setValue(snakeGameCode);
                
                // 如果程序名为空，自动填入默认名称
                var programNameInput = document.getElementById('program-name');
                if (programNameInput && !programNameInput.value.trim()) {
                    programNameInput.value = 'snake_game';
                }
            }
        });
    }
}); 
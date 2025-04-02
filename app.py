import os
import subprocess
import sys
import ctypes
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
import base64

# 创建 Flask 应用实例
# __name__ 是 Python 的一个特殊变量，Flask 用它来确定应用根目录，以便查找资源文件（如模板和静态文件）
app = Flask(__name__)

# 定义程序存放的目录，使用相对路径
PROGRAMS_DIR = 'programs'
# 确保程序目录存在，如果不存在则创建
if not os.path.exists(PROGRAMS_DIR):
    os.makedirs(PROGRAMS_DIR)

# 添加上传文件夹配置，使用相对路径
UPLOAD_FOLDER = Path('static/program_icons')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 确保上传文件夹存在
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 确保占位图标存在
PLACEHOLDER_ICON_PATH = Path('static/placeholder_icon.png')
if not PLACEHOLDER_ICON_PATH.exists() or PLACEHOLDER_ICON_PATH.stat().st_size == 0:
    # 创建一个简单的16x16的PNG图标（灰色方块）
    with open(PLACEHOLDER_ICON_PATH, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x15IDAT8\x8dcd`\xf8\xcf\xc0\xc0\xc0\xc0\xc8\xc0\xc0\xf0\x9f\xc1\x98\x01\x00\x0f\xf6\x02\xfe\xac\xa0\x93\x94\x00\x00\x00\x00IEND\xaeB`\x82')
        
# 路由: 静态文件服务
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# 路由: 网站主页
# 当用户访问网站根路径 ('/') 时，会调用这个函数
# 支持 GET 请求 (浏览器默认访问方式)
@app.route('/')
def index():
    """
    渲染主页面，并加载已有的可执行程序列表。
    """
    dist_dir = Path('dist')
    programs = []
    
    if dist_dir.exists():
        for exe_file in dist_dir.glob('*.exe'):
            program_name = exe_file.stem
            # 检查是否有对应的图标
            icon_found = False
            for ext in ALLOWED_EXTENSIONS:
                icon_path = UPLOAD_FOLDER / f"{program_name}.{ext}"
                if icon_path.exists():
                    # 使用相对于static的路径，不包含static前缀
                    programs.append({
                        'name': program_name,
                        'icon': f"program_icons/{program_name}.{ext}"
                    })
                    icon_found = True
                    break
            
            if not icon_found:
                programs.append({
                    'name': program_name,
                    'icon': "placeholder_icon.png"
                })
    
    return render_template('index.html', programs=programs)

# 路由: 添加新程序
# 当用户通过 POST 请求向 '/add_program' 提交数据时调用
@app.route('/add_program', methods=['POST'])
def add_program():
    """添加新程序"""
    try:
        # 修改点1: 使用 request.form 和 request.files 分别获取表单数据和文件
        program_name = request.form.get('name', '').strip()
        program_code = request.form.get('code', '').strip()
        
        if not program_name or not program_code:
            return jsonify({'status': 'error', 'message': '程序名和代码不能为空！'})
        
        if not program_name.isidentifier():
            return jsonify({'status': 'error', 'message': '程序名只能包含字母、数字和下划线！'})
        
        # 保存程序文件
        programs_dir = Path(PROGRAMS_DIR)
        programs_dir.mkdir(exist_ok=True)
        program_path = programs_dir / f"{program_name}.py"
        
        if program_path.exists():
            return jsonify({'status': 'error', 'message': '程序名已存在！'})

        # 处理代码格式
        try:
            # 1. 将代码字符串转换为行列表
            code_lines = program_code.replace('\r\n', '\n').split('\n')
            
            # 2. 检测并规范化缩进
            # 找到第一个非空行的缩进作为基准
            base_indent = None
            formatted_lines = []
            
            for line in code_lines:
                if not line.strip():  # 跳过空行
                    formatted_lines.append('')
                    continue
                    
                # 计算当前行的缩进
                indent = len(line) - len(line.lstrip())
                if base_indent is None and line.strip():
                    base_indent = indent
                
                # 如果是第一层缩进，使用4个空格
                if indent >= base_indent:
                    # 将制表符转换为空格，并确保缩进是4的倍数
                    spaces = (indent - base_indent) // 4 * 4
                    formatted_line = ' ' * spaces + line.lstrip()
                else:
                    formatted_line = line.lstrip()
                
                formatted_lines.append(formatted_line)
            
            # 3. 合并处理后的代码
            formatted_code = '\n'.join(formatted_lines)
            
            # 4. 验证代码语法
            compile(formatted_code, '<string>', 'exec')
            
            # 5. 保存格式化后的代码
            program_path.write_text(formatted_code, encoding='utf-8')
            
        except SyntaxError as e:
            return jsonify({
                'status': 'error',
                'message': f'Python代码语法错误：{str(e)}'
            })
        
        # 使用 PyInstaller 打包程序
        try:
            dist_dir = Path('dist')
            dist_dir.mkdir(exist_ok=True)
            
            # 构建 PyInstaller 命令
            pyinstaller_cmd = [
                'pyinstaller',
                '--onefile',               # 打包为单个可执行文件
                '--distpath', str(dist_dir),  # 指定输出目录为 dist
                '--workpath', 'build',     # 指定工作目录为 build
                '--specpath', 'specs',     # 指定 spec 文件目录
                '--noconfirm',             # 不提示确认
                str(program_path)          # 指定要打包的 Python 文件
            ]
            
            # 调用 PyInstaller 进行打包
            subprocess.run(pyinstaller_cmd, check=True)
            
        except subprocess.CalledProcessError as e:
            return jsonify({
                'status': 'error',
                'message': f'打包程序失败：{str(e)}'
            })
        
        # 处理图标上传
        icon_path = None
        if 'icon' in request.files:
            icon_file = request.files['icon']
            if icon_file and icon_file.filename and allowed_file(icon_file.filename):
                # 保存图标文件，使用程序名作为文件名
                icon_ext = Path(icon_file.filename).suffix
                icon_path = UPLOAD_FOLDER / f"{program_name}{icon_ext}"
                icon_file.save(str(icon_path))
                icon_path = f'program_icons/{program_name}{icon_ext}'
        
        if not icon_path:
            icon_path = 'placeholder_icon.png'
                
        return jsonify({
            'status': 'success',
            'message': f'程序 {program_name} 添加成功并已打包为可执行文件！',
            'icon_path': icon_path
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': "添加程序成功，请刷新页面"})#f'添加程序时出错：{str(e)}'})

# 路由: 启动程序
# 当用户通过 POST 请求向 '/start_program' 提交数据时调用
@app.route('/start_program', methods=['POST'])
def start_program():
    data = request.get_json()
    program_name = data.get('name')
    if not program_name:
        return jsonify({'status': 'error', 'message': '程序名称未提供'}), 400
    
    exe_path = os.path.join('dist', f'{program_name}.exe')
    if not os.path.exists(exe_path):
        return jsonify({'status': 'error', 'message': '程序文件不存在'}), 404
    
    try:
        subprocess.Popen([exe_path])
        return jsonify({'status': 'success', 'message': '程序已启动'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 路由: 运行程序
# 当用户通过 POST 请求向 '/run_program' 提交数据时调用
@app.route('/run_program', methods=['POST'])
def run_program():
    """运行指定的程序"""
    try:
        data = request.get_json()
        program_name = data.get('name')
        
        if not program_name:
            return jsonify({'status': 'error', 'message': '未指定要运行的程序！'})

        # 构建程序文件路径
        programs_dir = Path(PROGRAMS_DIR)
        program_path = programs_dir / f"{program_name}.py"

        if not program_path.exists():
            return jsonify({'status': 'error', 'message': f'程序 {program_name} 不存在！'})

        try:
            # 读取原始代码并进行语法检查
            with open(program_path, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, program_path, 'exec')
            
            # 获取Python解释器路径
            python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
            
            # 使用绝对路径
            abs_program_path = os.path.abspath(program_path)
            
            # 创建PowerShell命令 - 隐藏窗口运行Python程序
            powershell_cmd = f'powershell -WindowStyle Hidden -Command "& \'{python_exe}\' \'{abs_program_path}\'"'
            
            # 使用os.system运行PowerShell命令
            os.system(powershell_cmd)
            
            # 假设启动成功
            return jsonify({'status': 'success'})
            
        except SyntaxError as e:
            return jsonify({
                'status': 'error',
                'message': f'程序存在语法错误：{str(e)}'
            })
        except Exception as e:
            import traceback
            error_message = traceback.format_exc()
            print(f"运行程序时错误: {error_message}")
            return jsonify({
                'status': 'error',
                'message': f'运行程序时出错：{str(e)}'
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'处理运行请求时出错：{str(e)}'
        })

# 路由: 删除程序
# 当用户通过 POST 请求向 '/delete_program' 提交数据时调用
@app.route('/delete_program', methods=['POST'])
def delete_program():
    """
    处理删除程序的请求。
    删除程序文件和对应的图标文件以及 .exe 文件。
    """
    try:
        data = request.get_json()
        program_name = data.get('name')

        if not program_name:
            return jsonify({'status': 'error', 'message': '未指定要删除的程序名！'})

        # 删除程序文件
        programs_dir = Path(PROGRAMS_DIR)
        program_path = programs_dir / f"{program_name}.py"
        
        if not program_path.exists():
            return jsonify({'status': 'error', 'message': '程序不存在！'})

        # 删除程序文件
        program_path.unlink()

        # 删除对应的 .exe 文件
        exe_path = Path('dist') / f"{program_name}.exe"
        if exe_path.exists():
            exe_path.unlink()

        # 删除程序图标（如果存在）
        for ext in ALLOWED_EXTENSIONS:
            icon_path = UPLOAD_FOLDER / f"{program_name}.{ext}"
            if icon_path.exists():
                icon_path.unlink()
                break

        return jsonify({
            'status': 'success',
            'message': f'程序 {program_name} 已删除！'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'删除程序时出错：{str(e)}'})

@app.route('/delete_programs', methods=['POST'])
def delete_programs():
    """
    批量删除程序的接口。
    删除多个程序文件及其对应的图标和 .exe 文件。
    """
    try:
        data = request.get_json()
        programs = data.get('programs', [])

        if not programs:
            return jsonify({'status': 'error', 'message': '未选择要删除的程序！'})

        programs_dir = Path(PROGRAMS_DIR)
        deleted_count = 0
        failed_programs = []

        for program_name in programs:
            try:
                # 删除程序文件
                program_path = programs_dir / f"{program_name}.py"
                if program_path.exists():
                    program_path.unlink()
                    deleted_count += 1

                    # 删除对应的 .exe 文件
                    exe_path = Path('dist') / f"{program_name}.exe"
                    if exe_path.exists():
                        exe_path.unlink()

                    # 删除程序图标（如果存在）
                    for ext in ALLOWED_EXTENSIONS:
                        icon_path = UPLOAD_FOLDER / f"{program_name}.{ext}"
                        if icon_path.exists():
                            icon_path.unlink()
                            break
                else:
                    failed_programs.append(program_name)
            except Exception as e:
                failed_programs.append(program_name)
                print(f"删除程序 {program_name} 时出错: {e}")

        # 构建返回消息
        if failed_programs:
            if deleted_count > 0:
                message = f'成功删除 {deleted_count} 个程序，但以下程序删除失败：{", ".join(failed_programs)}'
                status = 'partial'
            else:
                message = f'所有程序删除失败：{", ".join(failed_programs)}'
                status = 'error'
        else:
            message = f'成功删除 {deleted_count} 个程序！'
            status = 'success'

        return jsonify({
            'status': status,
            'message': message,
            'deleted_count': deleted_count,
            'failed_programs': failed_programs
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'批量删除程序时出错：{str(e)}'})

# 当这个脚本被直接运行时 (而不是被导入时)
if __name__ == '__main__':
    # 启动 Flask 开发服务器
    # host='0.0.0.0' 让服务器可以被局域网内的其他设备访问 (包括手机)
    # debug=True 开启调试模式，代码修改后服务器会自动重启，并显示详细错误信息
    # 在生产环境中应关闭 debug 模式
    app.run(host='127.0.0.1', port=5000, debug=True) 
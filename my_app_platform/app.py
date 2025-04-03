import os
import subprocess
import sys
import ctypes
from flask import Flask, render_template, request, jsonify, send_from_directory, current_app
from flask_cors import CORS  # 添加CORS支持
from pathlib import Path
import shutil
import tempfile
import uuid
import json

# 创建 Flask 应用实例
# __name__ 是 Python 的一个特殊变量，Flask 用它来确定应用根目录，以便查找资源文件（如模板和静态文件）
app = Flask(__name__)
CORS(app)  # 启用CORS，允许跨域请求

# 增加请求超时设置
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用静态文件缓存
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 将最大请求大小提高到32MB

# 定义程序存放的目录，使用相对路径
PROGRAMS_DIR = 'programs'
# 确保程序目录存在，如果不存在则创建
if not os.path.exists(PROGRAMS_DIR):
    os.makedirs(PROGRAMS_DIR)

# 定义编译后EXE存储目录
EXE_DIR = 'exe_programs'
# 确保程序目录存在，如果不存在则创建
if not os.path.exists(EXE_DIR):
    os.makedirs(EXE_DIR)

# 添加上传文件夹配置，使用相对路径
UPLOAD_FOLDER = Path('static/program_icons')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'ico'} # Keep for potential future use or icon validation

# 确保上传文件夹存在
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 注释掉旧的，使用上面新的32MB设置

# 支持的编程语言及其打包命令
SUPPORTED_LANGUAGES = {
    'python': {
        'extension': '.py',
        'build_command': 'pyinstaller --onefile --noconsole --clean "{source_file}" --distpath "{output_dir}" --workpath "{temp_dir}" --specpath "{temp_dir}" --name "{program_name}"'
    } # Removed Java and C++ entries
}

# 确保占位图标存在
PLACEHOLDER_ICON_PATH = Path('static/placeholder_icon.png')
if not PLACEHOLDER_ICON_PATH.exists() or PLACEHOLDER_ICON_PATH.stat().st_size == 0:
    # 创建一个简单的16x16的PNG图标（灰色方块）
    try:
        with open(PLACEHOLDER_ICON_PATH, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x15IDAT8\x8dcd`\xf8\xcf\xc0\xc0\xc0\xc0\xc8\xc0\xc0\xf0\x9f\xc1\x98\x01\x00\x0f\xf6\x02\xfe\xac\xa0\x93\x94\x00\x00\x00\x00IEND\xaeB`\x82')
        print("Placeholder icon created.")
    except Exception as e:
        print(f"Error creating placeholder icon: {e}")

# 路由: 静态文件服务
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# 路由: 网站主页
@app.route('/')
def index():
    programs_dir = Path(PROGRAMS_DIR)
    programs = []
    if programs_dir.exists():
        for program_dir in programs_dir.iterdir():
            if program_dir.is_dir():
                info_file = program_dir / 'info.json'
                if info_file.exists():
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            program_info = json.load(f)
                            # Ensure icon path exists, otherwise use placeholder
                            icon_static_path = Path('static') / program_info.get('icon', 'placeholder_icon.png')
                            if not icon_static_path.exists():
                                program_info['icon'] = 'placeholder_icon.png'
                            programs.append(program_info)
                    except Exception as e:
                        print(f"Error reading program info {info_file}: {e}")
    return render_template('index.html', programs=programs)

# 路由: 添加新程序
@app.route('/add_program', methods=['POST'])
def add_program():
    try:
        program_name = request.form.get('name', '').strip()
        program_code = request.form.get('code', '').strip()
        program_language = request.form.get('language', 'python').strip().lower() # Default to python

        if not program_name or not program_code:
            return jsonify({'status': 'error', 'message': '程序名称和代码不能为空'})

        # Allow underscores in program names
        if not all(c.isalnum() or c == '_' for c in program_name):
             return jsonify({'status': 'error', 'message': '程序名称只能包含字母、数字和下划线'})

        if program_language != 'python': # Only support python now
            return jsonify({'status': 'error', 'message': f'不支持的编程语言：{program_language}'})

        programs_dir = Path(PROGRAMS_DIR)
        program_dir = programs_dir / program_name

        # Check if the directory exists and clean up if it's invalid/empty
        if program_dir.exists() and program_dir.is_dir():
            info_file = program_dir / 'info.json'
            # Check if directory is empty or lacks info.json
            if not info_file.exists() or not any(f for f in program_dir.iterdir() if f.name != 'info.json'):
                print(f"Removing potentially corrupt directory: {program_dir}")
                try:
                    shutil.rmtree(program_dir)
                except Exception as e:
                    print(f"Error removing corrupt directory {program_dir}: {e}")
                    return jsonify({'status': 'error', 'message': f'无法清理已存在的损坏目录 "{program_name}"'})
            else:
                return jsonify({'status': 'error', 'message': f'程序 "{program_name}" 已存在'})

        # Check Python syntax before saving
        try:
            compile(program_code, '<string>', 'exec')
        except SyntaxError as e:
            return jsonify({'status': 'error', 'message': f'Python代码语法错误：{str(e)}'})

        # Create program directory
        try:
             program_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
             print(f"Error creating directory {program_dir}: {e}")
             return jsonify({'status': 'error', 'message': f'创建程序目录失败: {e}'})


        # Save source code
        extension = SUPPORTED_LANGUAGES[program_language]['extension']
        source_file = program_dir / f'source{extension}'
        try:
            with open(source_file, 'w', encoding='utf-8') as f:
                f.write(program_code)
        except Exception as e:
            print(f"Error writing source file {source_file}: {e}")
            # Clean up created directory if saving fails
            shutil.rmtree(program_dir, ignore_errors=True)
            return jsonify({'status': 'error', 'message': f'保存源代码失败: {e}'})

        # Handle icon upload
        icon_file = request.files.get('icon')
        icon_filename = 'placeholder_icon.png' # Default relative to static

        if icon_file and icon_file.filename:
             # Basic check for allowed extensions
             file_ext = os.path.splitext(icon_file.filename)[1].lower()
             if file_ext[1:] in ALLOWED_EXTENSIONS: # Check without dot
                 # Use UUID for unique filename to avoid conflicts
                 icon_filename = str(uuid.uuid4()) + file_ext
                 icon_save_dir = UPLOAD_FOLDER # Use the Path object
                 icon_save_path = icon_save_dir / icon_filename
                 try:
                     icon_file.save(icon_save_path)
                     print(f"Icon saved to: {icon_save_path}")
                     # Store path relative to static dir
                     icon_filename = f"program_icons/{icon_filename}"
                 except Exception as e:
                     print(f"Error saving icon {icon_filename}: {e}")
                     icon_filename = 'placeholder_icon.png' # Revert to placeholder on save error
             else:
                 print(f"Invalid icon extension: {file_ext}")
                 # Optionally return an error here or just use placeholder
                 # return jsonify({'status': 'error', 'message': '不允许的图标文件类型'})


        # Build executable
        build_success, exe_path, error_message = build_executable(program_name, source_file, program_language)

        if not build_success:
            # Clean up created directory and source file if build fails
            shutil.rmtree(program_dir, ignore_errors=True)
            # Also remove uploaded icon if it wasn't the placeholder
            if icon_filename != 'placeholder_icon.png':
                 icon_to_remove = Path('static') / icon_filename
                 if icon_to_remove.exists():
                     try:
                         icon_to_remove.unlink()
                         print(f"Removed icon due to build failure: {icon_to_remove}")
                     except Exception as e:
                         print(f"Error removing icon {icon_to_remove}: {e}")

            return jsonify({'status': 'error', 'message': f'打包程序失败：{error_message}'})

        # Save program info
        program_info = {
            'name': program_name,
            'language': program_language,
            'source_file': str(source_file.relative_to(programs_dir)),
            'exe_path': exe_path, # Should be relative path like 'exe_programs/name/name.exe'
            'icon': icon_filename # Path relative to static/
        }

        try:
            with open(program_dir / 'info.json', 'w', encoding='utf-8') as f:
                json.dump(program_info, f, ensure_ascii=False, indent=4)
        except Exception as e:
             print(f"Error writing info.json for {program_name}: {e}")
             # Clean up everything if info saving fails
             shutil.rmtree(program_dir, ignore_errors=True)
             shutil.rmtree(Path(EXE_DIR) / program_name, ignore_errors=True)
             if icon_filename != 'placeholder_icon.png':
                  icon_to_remove = Path('static') / icon_filename
                  if icon_to_remove.exists(): icon_to_remove.unlink(missing_ok=True)
             return jsonify({'status': 'error', 'message': f'保存程序信息失败: {e}'})


        return jsonify({
            'status': 'success',
            'message': f'程序 "{program_name}" 添加并打包成功！',
            'icon_path': icon_filename # Send path relative to static/
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"添加程序时发生意外错误: {error_details}")
        return jsonify({'status': 'error', 'message': f'添加程序出错：{str(e)}'})

# 打包程序为可执行文件
def build_executable(program_name, source_file, language):
    print(f"开始打包程序: {program_name}, 语言: {language}")
    try:
        if language != 'python': # Only support python
            print(f"不支持的语言: {language}")
            return False, None, f"不支持的语言：{language}"

        # Log environment details
        print(f"Python Version: {sys.version}")
        print(f"Python Executable: {sys.executable}")
        print(f"Working Directory: {os.getcwd()}")
        print(f"Source File Path: {source_file} (Exists: {os.path.exists(source_file)})")

        exe_dir = Path(EXE_DIR) / program_name # Path where the final exe should be
        if not exe_dir.exists():
            try:
                exe_dir.mkdir(parents=True)
            except Exception as e:
                 print(f"Error creating EXE output directory {exe_dir}: {e}")
                 return False, None, f"创建EXE输出目录失败: {e}"

        print(f"EXE Output Directory: {exe_dir} (Exists: {exe_dir.exists()})")

        # Create temporary directory for build artifacts
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Temporary build directory: {temp_dir}")

            # Check Python syntax again (redundant but safe)
            try:
                print(f"Checking Python syntax...")
                with open(source_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                compile(source_code, str(source_file), 'exec')
                print("Python syntax OK.")
            except SyntaxError as e:
                print(f"Python Syntax Error: {e}")
                return False, None, f"Python代码语法错误: {str(e)}"

            # Verify source file exists before attempting build
            if not os.path.exists(source_file):
                print(f"Source file does not exist before build: {source_file}")
                return False, None, f"源文件不存在: {source_file}"

            # Prepare paths for PyInstaller command, ensuring quotes and correct separators
            source_file_str = str(source_file.absolute()).replace('\\', '/')
            output_dir_str = str(exe_dir.absolute()).replace('\\', '/') # PyInstaller --distpath needs absolute
            temp_dir_str = str(Path(temp_dir).absolute()).replace('\\', '/') # workpath/specpath need absolute

            cmd_template = SUPPORTED_LANGUAGES[language]['build_command']
            cmd = cmd_template.format(
                source_file=f'"{source_file_str}"',
                output_dir=f'"{output_dir_str}"',
                temp_dir=f'"{temp_dir_str}"',
                program_name=f'"{program_name}"' # Ensure program name is quoted if it contains spaces
            )

            print(f"Executing build command: {cmd}")

            try:
                # Log PATH environment variable
                print(f"PATH Environment Variable: {os.environ.get('PATH', 'Not Set')}")

                # Run PyInstaller
                process = subprocess.Popen(
                    cmd,
                    shell=True, # Often necessary on Windows for complex commands/paths
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.getcwd(), # Run from the project root context
                    encoding='utf-8', # Specify encoding for stdout/stderr
                    errors='ignore' # Ignore decoding errors
                )
                stdout, stderr = process.communicate(timeout=1200) # 20 min timeout

                print(f"Build process return code: {process.returncode}")
                print(f"Build stdout:\n{stdout}")
                print(f"Build stderr:\n{stderr}")

                if process.returncode != 0:
                    # Provide more specific error if possible
                    error_msg = f"打包失败 (返回码: {process.returncode})"
                    if stderr:
                         # Try to extract a key error message from PyInstaller output
                         lines = stderr.strip().split('\n')
                         if lines: error_msg += f": {lines[-1]}" # Use last line as potential summary
                         else: error_msg += f": {stderr[:200]}..." # Use first 200 chars
                    elif stdout: # Sometimes errors go to stdout
                         error_msg += f": {stdout[:200]}..."
                    return False, None, error_msg

            except subprocess.TimeoutExpired:
                process.kill()
                print("Build process timed out.")
                return False, None, "打包进程超时 (超过20分钟)，可能是程序过大或系统资源不足。"
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"Exception during build command execution: {e}")
                print(f"Traceback: {error_trace}")
                return False, None, f"执行打包命令时发生异常: {str(e)}"

            # Verify the expected executable file was created
            expected_exe_name = program_name + '.exe'
            final_exe_path = exe_dir / expected_exe_name # Absolute path

            print(f"Looking for generated EXE: {final_exe_path} (Exists: {final_exe_path.exists()})")

            if final_exe_path.exists():
                print(f"Successfully found EXE: {final_exe_path}")
                # 获取绝对路径字符串，并尝试用字符串操作计算相对路径
                try:
                    final_exe_abs_str = str(final_exe_path.resolve(strict=True))
                    exe_dir_base_abs_str = str(Path(EXE_DIR).resolve(strict=True))
                    print(f"Attempting string manipulation for relative path: EXE={final_exe_abs_str}, Base={exe_dir_base_abs_str}")

                    # 确保基础路径后有一个分隔符，以便正确匹配
                    if not exe_dir_base_abs_str.endswith(os.path.sep):
                        exe_dir_base_abs_str += os.path.sep

                    if final_exe_abs_str.startswith(exe_dir_base_abs_str):
                        # 截取相对路径部分
                        relative_exe_path = final_exe_abs_str[len(exe_dir_base_abs_str):]
                        print(f"Storing relative path via string manipulation: {relative_exe_path}")
                        return True, relative_exe_path, None
                    else:
                        print("EXE path does not start with base EXE dir path. Falling back.")
                        raise ValueError("String path prefix mismatch") # Trigger fallback

                except (ValueError, FileNotFoundError) as e:
                    print(f"Error calculating relative path from {final_exe_path} to {EXE_DIR} (using string method or fallback): {e}")
                    # 回退逻辑保持不变：尝试 CWD 相对路径，然后绝对路径
                    try:
                         cwd_path = Path.cwd().resolve() # Ensure CWD is resolved
                         # Ensure final_exe_abs_path is resolved if not already
                         if 'final_exe_abs_path' not in locals():
                              final_exe_abs_path = final_exe_path.resolve(strict=True)
                         fallback_relative_path = str(final_exe_abs_path.relative_to(cwd_path))
                         print(f"Fallback: Storing relative path to CWD {cwd_path}: {fallback_relative_path}")
                         return True, fallback_relative_path, None
                    except (ValueError, FileNotFoundError) as e2:
                         print(f"Fallback relative path calculation (to CWD) also failed: {e2}")
                         # 最终后备：如果连 CWD 相对路径也失败，直接存储绝对路径
                         if 'final_exe_abs_path' not in locals():
                              final_exe_abs_path = final_exe_path.resolve(strict=True)
                         print(f"Final Fallback: Storing absolute path: {final_exe_abs_path}")
                         return True, str(final_exe_abs_path), None # Store absolute path as last resort

            else:
                # List contents of the output directory if expected file not found
                print(f"Expected EXE not found. Contents of {exe_dir}:")
                try:
                     for item in exe_dir.glob('**/*'):
                         print(f"  - {item} (Is Dir: {item.is_dir()})")
                except Exception as list_e:
                    print(f"  Error listing directory contents: {list_e}")

                return False, None, "打包过程未生成预期的EXE文件，请检查PyInstaller日志。"

    except Exception as e:
        import traceback
        print(f"打包过程中发生意外错误: {e}")
        print(traceback.format_exc())
        return False, None, f"打包过程出错：{str(e)}"


# 路由: 运行程序
@app.route('/run_program', methods=['POST'])
def run_program():
    try:
        data = request.get_json()
        program_name = data.get('name')

        if not program_name:
            return jsonify({'status': 'error', 'message': '未提供程序名称'})

        programs_dir = Path(PROGRAMS_DIR)
        program_dir = programs_dir / program_name
        info_file = program_dir / 'info.json'

        if not info_file.exists():
            return jsonify({'status': 'error', 'message': f'程序信息文件 "info.json" 不存在于 {program_dir}'})

        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                program_info = json.load(f)
        except Exception as e:
            print(f"Error reading info.json {info_file}: {e}")
            return jsonify({'status': 'error', 'message': f'读取程序信息失败: {e}'})


        exe_relative_or_abs_path_str = program_info.get('exe_path')
        if not exe_relative_or_abs_path_str:
            return jsonify({'status': 'error', 'message': '程序信息中缺少可执行文件路径 (exe_path)'})

        exe_path_obj = Path(exe_relative_or_abs_path_str)
        exe_abs_path = None # Initialize

        # 检查存储的路径是否已经是绝对路径
        if exe_path_obj.is_absolute():
            if exe_path_obj.exists():
                exe_abs_path = exe_path_obj # 直接使用存储的绝对路径
                print(f"Using stored absolute path: {exe_abs_path}")
            else:
                print(f"Stored absolute path does not exist: {exe_path_obj}")
                return jsonify({'status': 'error', 'message': f'记录的绝对可执行文件路径无效或文件丢失: {exe_path_obj}'})
        else:
            # 存储的是相对路径，尝试解析
            # 优先相对于 EXE_DIR 解析
            potential_path1 = (Path(EXE_DIR).resolve() / exe_relative_or_abs_path_str).resolve() # Resolve combined path
            # 其次相对于 CWD 解析 (作为后备)
            potential_path2 = (Path.cwd() / exe_relative_or_abs_path_str).resolve() # Resolve combined path

            if potential_path1.exists():
                 exe_abs_path = potential_path1
                 print(f"Resolved relative path using EXE_DIR: {exe_abs_path}")
            elif potential_path2.exists():
                 exe_abs_path = potential_path2
                 print(f"Resolved relative path using CWD: {exe_abs_path}")
            else:
                 # 如果两种方式都找不到，则报告错误
                 print(f"Cannot find executable using relative path: {exe_relative_or_abs_path_str}")
                 print(f"Checked relative to EXE_DIR: {potential_path1}")
                 print(f"Checked relative to CWD: {potential_path2}")
                 return jsonify({'status': 'error', 'message': f'找不到可执行文件，相对路径无效: {exe_relative_or_abs_path_str}'})

        # 最终检查 exe_abs_path 是否有效且存在
        if not exe_abs_path or not exe_abs_path.exists():
            print(f"Executable file still not found or path invalid at final path: {exe_abs_path}")
            return jsonify({'status': 'error', 'message': f'最终计算的可执行文件路径无效: {exe_abs_path}'})

        # Use ShellExecuteW to run the program
        print(f"Attempting to run executable: {exe_abs_path}")
        SW_SHOWNORMAL = 1
        try:
             result = ctypes.windll.shell32.ShellExecuteW(
                 None,       # hwnd
                 "open",     # lpOperation
                 str(exe_abs_path), # lpFile
                 None,       # lpParameters
                 str(exe_abs_path.parent), # lpDirectory
                 SW_SHOWNORMAL # nShowCmd
             )
             print(f"ShellExecuteW result code: {result}")

             if result <= 32:
                 # Map common error codes
                 error_messages = {
                     0: "系统内存不足或资源耗尽", 2: "文件未找到", 3: "路径未找到", 5: "访问被拒绝",
                     8: "内存不足，无法完成操作", 11: "EXE格式无效", 26: "共享冲突",
                     27: "文件名关联不完整或无效", 28: "DDE事务失败", 29: "DDE事务超时",
                     30: "DDE事务已中止", 31: "目标应用程序没有响应", 32: "共享冲突"
                 }
                 error_msg = error_messages.get(result, f"未知错误，代码：{result}")
                 print(f"Failed to run program '{program_name}'. Error: {error_msg}")
                 return jsonify({'status': 'error', 'message': f'运行程序失败：{error_msg}'})

             print(f"Successfully launched program '{program_name}'")
             return jsonify({'status': 'success', 'message': '程序启动成功'}) # Keep success message for potential frontend use

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Exception during ShellExecuteW for {program_name}: {e}")
            print(f"Traceback: {error_trace}")
            return jsonify({'status': 'error', 'message': f'运行程序时发生系统错误：{str(e)}'})

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"运行程序路由时发生意外错误: {e}")
        print(f"Traceback: {error_trace}")
        return jsonify({'status': 'error', 'message': f'运行程序出错：{str(e)}'})


# 路由: 批量删除程序
@app.route('/delete_programs', methods=['POST'])
def delete_programs():
    try:
        data = request.get_json()
        program_names = data.get('programs', [])

        if not program_names:
            return jsonify({'status': 'error', 'message': '未选择要删除的程序'})

        # 确保使用绝对路径
        programs_dir = Path(PROGRAMS_DIR).resolve()
        exe_dir = Path(EXE_DIR).resolve()

        success_count = 0
        errors = []

        for program_name in program_names:
            program_dir = programs_dir / program_name
            program_exe_dir = exe_dir / program_name
            icon_path = None
            error_messages = []

            # 获取图标路径
            info_file = program_dir / 'info.json'
            if info_file.exists():
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        program_info = json.load(f)
                        icon_relative = program_info.get('icon', '')
                        if icon_relative and icon_relative != 'placeholder_icon.png':
                            # 构造静态文件绝对路径
                            icon_path = Path(current_app.static_folder) / icon_relative
                except Exception as e:
                    error_messages.append(f"读取图标信息失败: {str(e)}")

            # 删除源代码目录
            try:
                shutil.rmtree(program_dir)
                print(f"已删除源代码目录: {program_dir}")
            except FileNotFoundError:
                print(f"源代码目录不存在: {program_dir}")
            except Exception as e:
                error_messages.append(f"删除源代码失败: {str(e)}")

            # 删除EXE目录
            try:
                shutil.rmtree(program_exe_dir)
                print(f"已删除EXE目录: {program_exe_dir}")
            except FileNotFoundError:
                print(f"EXE目录不存在: {program_exe_dir}")
            except Exception as e:
                error_messages.append(f"删除EXE文件失败: {str(e)}")

            # 删除图标文件
            if icon_path:
                try:
                    icon_path.unlink()
                    print(f"已删除图标: {icon_path}")
                except FileNotFoundError:
                    print(f"图标文件不存在: {icon_path}")
                except Exception as e:
                    error_messages.append(f"删除图标失败: {str(e)}")

            # 统计结果
            if not error_messages:
                success_count += 1
            else:
                errors.append(f"程序 '{program_name}': {', '.join(error_messages)}")

        # 构造响应
        if success_count == len(program_names):
            return jsonify({'status': 'success', 'message': f'成功删除 {success_count} 个程序'})
        elif success_count > 0:
            return jsonify({
                'status': 'partial',
                'message': f'部分成功（{success_count}/{len(program_names)}）',
                'errors': errors
            })
        else:
            return jsonify({'status': 'error', 'message': '删除失败', 'errors': errors})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'})

# 清理所有程序（包括旧格式和空目录）
@app.route('/clean_all_programs', methods=['POST'])
def clean_all_programs():
    print("开始清理所有程序...")
    programs_dir = Path(PROGRAMS_DIR)
    exe_dir = Path(EXE_DIR)
    icon_dir = Path('static/program_icons')
    errors = []

    # Clean programs directory
    if programs_dir.exists():
        print(f"清理目录: {programs_dir}")
        for item in programs_dir.iterdir():
            try:
                if item.is_dir():
                    print(f"  删除子目录: {item}")
                    shutil.rmtree(item)
                elif item.is_file(): # Should not happen with current structure, but clean anyway
                    print(f"  删除文件: {item}")
                    item.unlink()
            except Exception as e:
                err_msg = f"删除 {item} 时出错: {e}"
                print(f"  错误: {err_msg}")
                errors.append(err_msg)

    # Clean EXE directory
    if exe_dir.exists():
        print(f"清理目录: {exe_dir}")
        for item in exe_dir.iterdir():
            try:
                if item.is_dir():
                    print(f"  删除子目录: {item}")
                    shutil.rmtree(item)
                elif item.is_file():
                    print(f"  删除文件: {item}")
                    item.unlink()
            except Exception as e:
                err_msg = f"删除 {item} 时出错: {e}"
                print(f"  错误: {err_msg}")
                errors.append(err_msg)

    # Clean icons directory (excluding placeholder)
    if icon_dir.exists():
        print(f"清理目录: {icon_dir}")
        for icon in icon_dir.iterdir():
            # Keep placeholder and potentially default icon if needed later
            if icon.is_file() and icon.name not in ['placeholder_icon.png', 'default_icon.png']:
                 try:
                    print(f"  删除图标: {icon}")
                    icon.unlink()
                 except Exception as e:
                     err_msg = f"删除图标 {icon} 时出错: {e}"
                     print(f"  错误: {err_msg}")
                     errors.append(err_msg)

    if not errors:
        return jsonify({'status': 'success', 'message': '所有程序已成功清理完毕'})
    else:
        error_summary = '，'.join(errors)
        return jsonify({'status': 'error', 'message': f'清理程序时发生错误：{error_summary}'})


# 当这个脚本被直接运行时 (而不是被导入时)
if __name__ == '__main__':
    # 启动 Flask 开发服务器
    # host='127.0.0.1' 仅本地访问
    # debug=True 开启调试模式，显示详细错误信息
    # use_reloader=False 禁用自动重载，防止因文件变动导致频繁重启
    print("Starting Flask server...")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False) 
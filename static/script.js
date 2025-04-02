/**
 * @fileoverview 前端交互逻辑，处理程序运行、添加和删除。
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');

    // ----- 获取页面元素 -----
    var programsContainer = document.getElementById('programs-container');
    var addProgramSection = document.getElementById('add-program');
    var deleteProgramsSection = document.getElementById('delete-programs');
    var addProgramForm = document.getElementById('add-program-form');
    var deleteProgramsForm = document.getElementById('delete-programs-form');
    var addMessageDiv = document.getElementById('add-message');
    var deleteMessageDiv = document.getElementById('delete-message');
    
    // 菜单相关元素
    var dropdown = document.querySelector('.dropdown');
    var menuButton = document.querySelector('.menu-button');
    var showAddFormButton = document.getElementById('show-add-form-button');
    var showDeleteFormButton = document.getElementById('show-delete-form-button');
    var cancelAddButton = document.getElementById('cancel-add-button');
    var cancelDeleteButton = document.getElementById('cancel-delete-button');
    var selectAllButton = document.getElementById('select-all-button');
    var deselectAllButton = document.getElementById('deselect-all-button');
    
    // 打印关键元素是否存在
    console.log('关键元素检查:', {
        addProgramSection: addProgramSection ? true : false,
        deleteProgramsSection: deleteProgramsSection ? true : false,
        programsContainer: programsContainer ? true : false
    });
    
    // ----- 绑定菜单点击事件 -----
    
    // 添加程序按钮
    var addBtn = document.getElementById('show-add-form-button');
    if (addBtn) {
        addBtn.addEventListener('click', function(e) {
            console.log('点击添加程序按钮');
            e.stopPropagation(); // 防止事件冒泡
            
            // 获取表单元素
            var addForm = document.getElementById('add-program');
            var deleteForm = document.getElementById('delete-programs');
            
            // 切换显示状态
            if (addForm) {
                addForm.style.display = 'block';
                addForm.classList.remove('hidden');
            }
            
            if (deleteForm) {
                deleteForm.style.display = 'none';
                deleteForm.classList.add('hidden');
            }
            
            // 关闭下拉菜单
            document.querySelector('.dropdown').classList.remove('active');
        });
    }
    
    // 批量删除按钮
    var deleteBtn = document.getElementById('show-delete-form-button');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function(e) {
            console.log('点击批量删除按钮');
            e.stopPropagation(); // 防止事件冒泡
            
            // 获取表单元素
            var addForm = document.getElementById('add-program');
            var deleteForm = document.getElementById('delete-programs');
            
            // 切换显示状态
            if (deleteForm) {
                deleteForm.style.display = 'block';
                deleteForm.classList.remove('hidden');
            }
            
            if (addForm) {
                addForm.style.display = 'none';
                addForm.classList.add('hidden');
            }
            
            // 关闭下拉菜单
            document.querySelector('.dropdown').classList.remove('active');
        });
    }
    
    // 取消添加按钮
    var cancelAddBtn = document.getElementById('cancel-add-button');
    if (cancelAddBtn) {
        cancelAddBtn.addEventListener('click', function() {
            console.log('点击取消添加按钮');
            var addForm = document.getElementById('add-program');
            if (addForm) {
                addForm.style.display = 'none';
                addForm.classList.add('hidden');
            }
        });
    }
    
    // 取消删除按钮
    var cancelDeleteBtn = document.getElementById('cancel-delete-button');
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', function() {
            console.log('点击取消删除按钮');
            var deleteForm = document.getElementById('delete-programs');
            if (deleteForm) {
                deleteForm.style.display = 'none';
                deleteForm.classList.add('hidden');
            }
        });
    }
    
    // 菜单按钮
    document.querySelector('.menu-button').onclick = function(e) {
        console.log('点击菜单按钮');
        e.stopPropagation();
        document.querySelector('.dropdown').classList.toggle('active');
    };
    
    // 点击其他地方关闭菜单
    document.addEventListener('click', function() {
        document.querySelector('.dropdown').classList.remove('active');
    });
    
    // 防止菜单内容点击关闭菜单
    document.querySelector('.dropdown-content').onclick = function(e) {
        e.stopPropagation();
    };
    
    // ----- 程序启动功能 -----
    function handleProgramStart(event) {
        console.log('启动程序按钮被点击', event.target);
        
        var programItem = event.target.closest('.program-item');
        if (!programItem) return;
        
        var programName = programItem.dataset.programName;
        console.log('启动程序:', programName);
        
        if (programItem.getAttribute('data-processing') === 'true') {
            console.log('程序正在处理中');
            return;
        }
        
        programItem.setAttribute('data-processing', 'true');
        programItem.style.opacity = '0.7';
        
        // 发送请求启动程序
        fetch('/start_program', {
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
            console.error('启动程序出错:', error);
            alert('启动程序出错: ' + error);
        })
        .finally(function() {
            programItem.style.opacity = '1';
            programItem.removeAttribute('data-processing');
        });
    }

    // 绑定程序点击事件
    if (programsContainer) {
        programsContainer.addEventListener('click', handleProgramStart);
    }
    
    // ----- 添加程序功能 -----
    
    // 提交添加程序表单
    if (addProgramForm) {
        addProgramForm.onsubmit = function(event) {
            event.preventDefault();
            console.log('提交添加程序表单');
            
            var programName = document.getElementById('program-name').value.trim();
            var programCode = document.getElementById('program-code').value;
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
            
            var formData = new FormData();
            formData.append('name', programName);
            formData.append('code', programCode);
            
            if (programIcon.files.length > 0) {
                formData.append('icon', programIcon.files[0]);
            }
            
            fetch('/add_program', {
                method: 'POST',
                body: formData
            })
            .then(function(response) { return response.json(); })
            .then(function(result) {
                if (result.status === 'success') {
                    // 成功后操作
                    addProgramForm.reset();
                    document.getElementById('add-program').classList.add('hidden');
                    alert(result.message);
                    addNewProgram(programName, result.icon_path);
                } else {
                    // 错误处理
                    showMessage(addMessageDiv, result.message, result.status);
                }
            })
            .catch(function(error) {
                console.error('添加程序出错:', error);
                showMessage(addMessageDiv, '添加程序出错: ' + error, 'error');
            });
        };
    }
    
    // ----- 删除程序功能 -----
    
    // 全选按钮
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
                    
                    document.getElementById('delete-programs').classList.add('hidden');
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
    function addNewProgram(programName, iconPath) {
        var gridSection = document.getElementById('program-grid');
        var container = document.getElementById('programs-container');
        
        // 如果网格不存在，创建新的网格
        if (!gridSection) {
            gridSection = document.createElement('section');
            gridSection.id = 'program-grid';
            
            container = document.createElement('div');
            container.id = 'programs-container';
            container.addEventListener('click', handleProgramStart);
            
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
        
        var iconImg = document.createElement('img');
        iconImg.src = '/static/' + iconPath;
        iconImg.alt = programName + ' 图标';
        iconImg.className = 'program-icon';
        
        var nameSpan = document.createElement('span');
        nameSpan.className = 'program-name';
        nameSpan.textContent = programName;
        
        newItem.appendChild(iconImg);
        newItem.appendChild(nameSpan);
        container.appendChild(newItem);
    }
}); 
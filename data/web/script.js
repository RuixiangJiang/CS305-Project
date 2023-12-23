// 监听注册和登录按钮的提交事件
document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const encodedCredentials = btoa(username + ':' + password);

    // 发送登录请求到服务器
    fetch('/login', {
        method: 'POST',
        headers: {
            'Authorization': 'Basic ' + encodedCredentials,
        }
    })
    .then(response => {
        if (!response.ok) { // 检查响应状态码
            throw new Error(`登录失败, 错误: ${response.status} ${response.statusText}`);
        }
        return response.text(); 
    })
    .then(text => {
        // 登录成功后的处理，如重定向
        window.location.href = '/';
    })
    .catch(error => {
        // 处理错误情况，如显示一个错误消息
        alert(error.message);
        console.error('登录请求失败:', error);
    });
});


document.getElementById('registerForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const username = document.getElementById('newUsername').value;
    const password = document.getElementById('newPassword').value;
    const encodedCredentials = btoa(username + ':' + password);

    // 发送注册请求到服务器
    fetch('/register', {
        method: 'POST',
        headers: {
            'Authorization': 'Basic ' + encodedCredentials,
        }
    })
    .then(response => {
        if (!response.ok) { 
            throw new Error(`注册失败, 错误: ${response.status} ${response.statusText}`);
        }
        return response.text();
    })
    .then(text => {
        window.location.href = '/';
    })
});

// Functions

function uploadFile() {
    // Get the file input element
    var fileInput = document.getElementById('fileInput');
    
    // Get the selected file
    var file = fileInput.files[0];

    if (!file) {
        alert("请选择文件！");
        return;
    }

    // Create a FormData object to send the file as part of the POST request
    var formData = new FormData();
    formData.append('file', file);

    // Create a Fetch API POST request to the server
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            alert("文件已上传！");
            // Optionally, you can reload the page or update the file listing
            location.reload();
        } else {
            alert("上传文件失败！");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("发生错误，无法上传文件！");
    });
}

function deleteFile(filePath) {
    if (confirm("确认删除文件？")) {
        // Send an asynchronous request to the server to delete the file
        fetch(`/delete?file=${encodeURIComponent(filePath)}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                alert("文件已删除！");
                // Optionally, you can reload the page or update the file listing
                location.reload();
            } else {
                alert("删除文件失败！");
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("发生错误，无法删除文件！");
        });
    }
}

function downloadFile(filePath, sustechHttp) {
    alert(`Downloading ${filePath}\nwith SUSTech-HTTP code: ${sustechHttp}`);

    if (sustechHttp == 1) {
        //fetch(`/download?file=${encodeURIComponent(filePath)}`, {
        fetch(`${filePath}?SUSTech-HTTP=1`, {
            method: 'GET'
        })
        .then(response => {
            if (response.ok) {
                return response.text(); // 假设响应是文本类型
            } else {
                throw new Error('获取数据失败');
            }
        })
        .then(text => {
            alert(text);
        })
        .catch(error => {
            alert(error.message);
            console.error('获取数据时发生错误:', error);
        });
    }
    else {
        // It's a file, perform regular download
        var link = document.createElement('a');
        link.download = filePath.split('/').pop();
        link.href = filePath;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}
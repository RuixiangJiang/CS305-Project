import os


def parse_query_params(request_data):
    # Extract query string from request_data
    _, _, query_string = request_data.partition("\r\n\r\n")

    # Parse query parameters
    query_params = {}
    for param in query_string.split("&"):
        key_value = param.split("=")
        key = key_value[0]
        value = key_value[1] if len(key_value) > 1 else ''
        query_params[key] = value

    return query_params


def percent_encode_url(url):
    return url


def send_directory_listing(client_socket, dir_path, request):
    query_params = parse_query_params(request)
    sustech_http = int(query_params.get('SUSTech-HTTP', '0'))
    print("sustech-http =", sustech_http)
    file_list = os.listdir(dir_path)
    content = """
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <script>
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
                    alert(filePath + " " + sustechHttp);
                
                    if (sustechHttp == 1) {
                        // to do
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
            </script>

        </head>
        <body>
            <h1>File Listing</h1>
            <input type="file" id="fileInput">
            <button onclick="uploadFile()">Upload</button>
            <ul>
    """
    content += f'<li><a href="{percent_encode_url("..")}">返回上一级</a></li>'
    content += f'<li><a href="{percent_encode_url("/")}">返回根目录</a></li>'

    for file in file_list:
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            file += "/"
            content += f'''
                <li>
                    <a href="{percent_encode_url(file)}">{file}</a> 
                    <button onclick="deleteFile('{percent_encode_url(file)}')">Delete</button>
                    <button onclick="downloadFile('{percent_encode_url(file)}', 0)">Download (SUSTech-HTTP=0)</button>
                    <button onclick="downloadFile('{percent_encode_url(file)}', 1)">Download (SUSTech-HTTP=1)</button>
                </li>
            '''
        else:
            content += f'''
                <li>
                    <a href="{percent_encode_url(file)}">{file}</a> 
                    <button onclick="deleteFile('{percent_encode_url(file)}')">Delete</button>
                    <button onclick="downloadFile('{percent_encode_url(file)}', 0)">Download</button>
                </li>
            '''

    content += """
            </ul>
        </body>
        </html>
    """

    content_encoded = content.encode("utf-8")
    response_headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(content_encoded)}\r\n\r\n"
    client_socket.send(response_headers.encode('utf-8') + content_encoded)

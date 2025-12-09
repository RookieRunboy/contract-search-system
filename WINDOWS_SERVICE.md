# Windows 守护与自启动示例

本文档给出在 Windows 上守护后端进程的参考做法，不影响 Linux/macOS 脚本。假设代码路径为 `C:\contract_search_system`（请按实际路径替换），Python 3.12 已在 PATH 中，已运行过 `start_windows.ps1` 安装依赖。

## NSSM（简单快捷）
1. 安装 NSSM（解压后将 `nssm.exe` 放入 PATH）。
2. 注册服务：
   ```powershell
   nssm install contract-search-backend "C:\Python312\python.exe" "-m uvicorn contractApi:app --host 0.0.0.0 --port 8006 --workers 2"
   nssm set contract-search-backend AppDirectory "C:\contract_search_system\backend"
   nssm set contract-search-backend AppStdout "C:\contract_search_system\logs\backend_service.out.log"
   nssm set contract-search-backend AppStderr "C:\contract_search_system\logs\backend_service.err.log"
   nssm set contract-search-backend Start SERVICE_AUTO_START
   nssm set contract-search-backend AppThrottle 1500
   ```
3. 启动 / 停止 / 删除：
   ```powershell
   nssm start contract-search-backend
   nssm stop contract-search-backend
   nssm remove contract-search-backend confirm
   ```
   如需使用虚拟环境，替换可执行路径为 `C:\contract_search_system\contract_env\Scripts\python.exe`。

## WinSW（XML 模板）
1. 下载 WinSW 可执行文件（命名为 `winsw.exe`）放到 `C:\contract_search_system\service\`。
2. 创建 `C:\contract_search_system\service\contract-search-backend.xml`：
   ```xml
   <service>
     <id>contract-search-backend</id>
     <name>Contract Search Backend</name>
     <description>FastAPI backend for contract search</description>
     <executable>C:\Python312\python.exe</executable>
     <arguments>-m uvicorn contractApi:app --host 0.0.0.0 --port 8006 --workers 2</arguments>
     <workingdirectory>C:\contract_search_system\backend</workingdirectory>
     <logpath>C:\contract_search_system\logs</logpath>
     <log mode="roll-by-size">
       <sizeThreshold>10240</sizeThreshold>
       <keepFiles>5</keepFiles>
     </log>
     <onfailure action="restart" delay="5 sec"/>
   </service>
   ```
   调整 `executable` 与 `workingdirectory` 路径；若使用虚拟环境，将 `executable` 指向 `contract_env\Scripts\python.exe`。
3. 安装 / 启动：
   ```powershell
   cd C:\contract_search_system\service
   .\winsw.exe install
   .\winsw.exe start
   ```
   停止或移除：`.\winsw.exe stop` / `.\winsw.exe uninstall`。

## 配合 stop_windows.ps1
- 如未使用服务守护，可通过 `.\stop_windows.ps1 [-StopElasticsearch]` 停止 `start_windows.ps1` 启动的后端，并可选停止 Docker 容器 `es`。
- 服务化后，建议用 NSSM/WinSW 的 stop 命令控制后端；`stop_windows.ps1` 仍可用于清理手工启动的实例。

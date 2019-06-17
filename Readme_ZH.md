## 使用说明

### 安装

以 python3 环境为例：

1. 在MySQL中建立数据库

   ```mysql
   create database shadowsocks;
   grant all privileges on shadowsocks.* to 'yourdbusername'@'%' identified by 'yourpassword';
   quit
   ```

2. 在 bash 下导入 sql 模板文件

   ```bash
   mysql -uyourdbusername -pyourpassword shadowsocks < shadowsocks.sql
   ```

3. 安装该程序包

    ``` bash
    git clone https://github.com/dylanchu/ss-py-mu.git
    cd ss-py-mu
    sudo python3 setup.py install -f
    ```
    
4. 更改配置文件

   至此，你已经安装好了该程序，运行试一下：

   ```bash
   ss-py-mu
   ```

   正常情况你会看到提示让你更改配置文件 `/root/.config/ss-py-mu/config.ini`，按要求更改即可。更改后再次运行程序，如果没有报错信息，说明一切顺利，按 `ctrl+c` 可以结束运行。



### 使用 supervisor 监控程序运行

1. supervisor 能监控程序的运行并记录输出到日志文件，并且能在程序意外退出时自动重启程序

1. 在 */etc/supervisor/conf.d/* 中新建 *ss-py-mu.conf* 文件并输入以下内容：
	```
	[program:ss-py-mu]
	command = ss-py-mu
	user=root
	autostart = true
	autorestart = true
	stdout_logfile = /var/log/supervisor/ss-py-mu_stdout.log
	stderr_logfile = /var/log/supervisor/ss-py-mu_stderr.log
	```

3. 使用 supervisor 启动程序

   ```bash
   supervisorctl reread
   supervisorctl reload
   ```



### 多用户版本和原版有什么不同

多用户版本开启了 3 个线程：

- ss-manager
- thread_pull 从数据库读取配置，并通过 udp 发送到 `ss-manager`
- thread_push 从 `ss-manager` 读取使用流量等信息并发送到数据库

原版以很久未更新，对python3的支持也不好。除了这些兼容性上的改进，功能上的改动主要体现在以下文件：（均在 `shadowsocks` 文件夹下）

- servers.py
- dbtransfer.py
- config.py / config_default.ini / config_template.ini
- constant.py
- 数据库模板文件 shadowsocks.sql / shadowsocks-minimal.sql

此外，多用户版还在 `manager.py` 的日志中记录了用户端口和邮箱信息，通过改动 `tcprelay.py` 和 `udprelay.py` 添加了端口黑/白名单功能。

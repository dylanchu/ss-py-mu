About ss-py-mu

This project is based on  [fsgmhoward's version](<https://github.com/fsgmhoward/shadowsocks-py-mu>). I JUST change the database structure and fix bugs on the original code to work with python3.

## shadowsocks

A fast tunnel proxy that helps you bypass firewalls.

## Install

Please use python3.

1. Setup database in MySQL.

   ```mysql
   create database shadowsocks;
   grant all privileges on shadowsocks.* to 'yourdbusername'@'%' identified by 'yourpassword';
   quit
   ```

2. Import database template in bash

   ```bash
   mysql -uyourdbusername -pyourpassword shadowsocks < shadowsocks.sql
   ```

3. Install the package

    ``` bash
    git clone https://github.com/dylanchu/ss-py-mu.git
    cd ss-py-mu
    sudo python3 setup.py install -f
    ```
    
4. Config your program

   Try to launch `ss-py-mu` first:

   ```bash
   ss-py-mu
   ```

   Normally you'll see the instructions to edit your config file `/root/.config/ss-py-mu/config.ini` . After you have done that, run `ss-py-mu` again. If it runs ok then everything is ok. You can press `ctrl+c` to terminate the program.
   



## Use supervisor to monitor ss-py-mu

1. Supervisor can monitor you program and log the output to a log file. And it can restart your program if it stops because of unexpected reasons.

1. You will need to create a file `ss-py-mu.conf` under the folder  `/etc/supervisor/conf.d/`. Contents should be like:
	```
	[program:ss-py-mu]
	command = ss-py-mu
	user=root
	autostart = true
	autorestart = true
	stdout_logfile = /var/log/supervisor/ss-py-mu_stdout.log
	stderr_logfile = /var/log/supervisor/ss-py-mu_stderr.log
	```

3. Start your program with supervisor.

   ```bash
   supervisorctl reread
   supervisorctl reload
   ```



# Tornado-Debug

Tornado Web应用程序调试工具. 统计应用在处理网络请求时的多项指标．

指标包括：

* handlers的各个函数的执行情况，包括调用关系、次数、时间
* redis 操作的每个指令的内容、次数、时间
* urllib/urllib2 发起的每个网络请求的url、次数、时间

### INSTALL

python setup.py install

### USAGE

tor-debug <python command>

eg: tor-debug python -m wcms_front.server --profile=dev

### LICENSE

under MIT
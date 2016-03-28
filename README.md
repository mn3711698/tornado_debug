# Tornado-Debug

Tornado Web应用程序调试工具. 统计应用在处理网络请求时的多项指标．

指标包括：

* handlers的各个函数的执行情况，包括调用关系、次数、时间
* redis 操作的每个指令的内容、次数、时间
* urllib/urllib2 发起的每个网络请求的url、次数、时间

### INSTALL

    python setup.py install

### USAGE

#### 本地调试

    tor-debug [python command]

    eg: tor-debug python -m wcms_front.server --profile=dev

#### 服务模式

在此模式下， tornado_debug 持续收集测试数据，并把监控数据发往本定的8888端口。 统计接口可以通过访问http://host:8888/看到。

    export TOR_DEBUG_SERVER_MODE=1
    tor-debug [python command]

### LICENSE

under MIT

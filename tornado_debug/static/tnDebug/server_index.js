function drawCharts(chartsId, chartsTitle, dataObj){
    var series=[];

    for(var key in dataObj){
        var item = {name: key, data:[]};
        var points = [];
        if(dataObj[key].length > 1500){
            points = dataObj[key].splice(-1500);
        }else{
            points = dataObj[key];
        }
        for(var i in points){
            var point = {};
            data = points[i];
            point.x = parseFloat(data.start_time*1000);
            point.y = parseFloat(data.time_use);
            point.url = data.url.split('?')[0];
            point.id = data.id;
            item.data.push(point);
        }
        series.push(item);
    }
    Highcharts.setOptions({
        global: {
            timezoneOffset: -8 * 60
        }
    });
    $('#'+chartsId).highcharts({
        rangeSelector: {
            allButtonsEnabled: true
        },
        plotOptions: {
            series: {
                cursor: 'pointer',
                point: {
                    events: {
                        click: function () {
                            location.href = '/detail/' + this.options.id;
                        }
                    }
                },
                turboThreshold: 1500
            }
        },
        chart: {
            type: 'line',
            zoomType: 'x'
        },
        title: {
            text: chartsTitle
        },
        xAxis: {
            type: 'datetime',
        },
        yAxis: {
            title: {
                text: '访问时间(ms)',
            }
        },
        tooltip: {
            pointFormat: ' <span style="color:{point.color}">\u25CF</span> {point.options.url}: <b>{point.y}ms</b><br/>',
        },
        series: series
    });
}

$(
function(){
    $.get('/api/list', function(dataObj){
        drawCharts('container', '横向访问速度曲线', dataObj);
    });

    function drawCompareCharts(url){
        $("#dropdownUrls span").first().text(url);
        var url_encode = encodeURIComponent(url);
        $.get('/api/list/compare?url='+url_encode, function(data){
            drawCharts('container2', '纵向访问时间曲线',data);
        });
    }
    
    $(".dropdown ul li").click(function(){
        var url = $(this).text();
        drawCompareCharts(url);
    });

    drawCompareCharts("/n/");
}
);

function init(){

    var initApi = {

        redisInit: function(){ 

            function getTr(args, count, time){
                var shortArgs = args.substr(0, 20);
                if (shortArgs.length < args.length){
                    shortArgs += '...';
                }
                var html = '<tr><th>' + shortArgs + "</th>"+
                    "<th>" + count + "</th>" +
                    "<th>" + time + "</th></tr>";
                return html;
            }

            var tooltip = '<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner" style="max-width: none;"></div></div>';

            var rightTable = $("#tn-redis-right tbody");

            $("#tn-redis-left tbody tr").on('click', function(){
                var commdName = $(this).find('th:first-child').text();
                var detail_id = "tn-" + commdName;
                rightTable.html("");
                $("#"+detail_id).find('div.detail-row').each(function(){
                    var detail_html = $(this).find('div');
                    var args = $(detail_html[0]).text();
                    var count = $(detail_html[1]).text();
                    var time = $(detail_html[2]).text();

                    var html = getTr(args, count, time);
                    rightTable.append(html);

                    function getTitle(){
                        $('#redis-json').JSONView(JSON.parse(args));
                        return $("#redis-json").html();
                    }
                    rightTable.find('tr:last-child th:first-child').tooltip({'placement': 'bottom', 'title': getTitle, 'template': tooltip, 'html': true, 'trigger': 'click'});
                });

            });
        },

        tornadoInit: function(){
            
            var tornadoData = $('#tornado-data').text();
            var jsonData = JSON.parse(tornadoData);
            $('#tornado-json').JSONView(jsonData, {collapsed: true, nl2br: true});
            $('#tornado-json').JSONView('expand', 1);
            // when click childern + , expend all childern node
            $('#tornado-json .collapser').bind('click', function(){
                // this is the second event handler, so the text is '-'
                if($(this).text() == '-'){
                    var prop = $(this).siblings('span.prop');
                    console.log(prop);
                    if(prop.length<1){
                        return;
                    }
                    var collapsible = $(this).siblings("ul.collapsible");
                    if(collapsible.length < 1){
                        return;
                    }
                    collapsible = collapsible[0];
                    $(collapsible).children("li").each(function(){
                        $(this).children("div.collapser").each(function(){
                            if($(this).text()=="+"){
                                $(this).click();
                            }
                        });
                    });
                }
            });
            
           function changeFace(){
                if($('#tornado-table').css('display')=='none'){
                    $('#tornado-json').hide();
                    $('#tornado-table').show();
                }else{
                    $('#tornado-table').hide();
                    $('#tornado-json').show();
                }
           }

           $('#showTable').click(function(){
                if($('#tornado-table').css('display')=='none'){
                    changeFace();
                } 
           });

           $('#showJson').click(function(){
                if($('#tornado-json').css('display')=='none'){
                    changeFace();
                } 
           });

           $('#tornado-table').show();
            
        },

        responseInit: function(){
            if($("#response-data").length === 0){
                return;
            }
            try{
                var respData = $('#response-data').text();
                var respJson = JSON.parse(respData);
                $('#response-json').JSONView(respJson, {collapsed: true, nl2br: true});
                $('#respJson-json').JSONView('expand', 1);
                $("#response-json").show();
            }catch(e){
                $("#response-data").show();
            }
        }
    };

    initApi.tornadoInit();
    initApi.redisInit();
    initApi.responseInit();
}

$(document).ready(init);

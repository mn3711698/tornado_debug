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
                    rightTable.find('tr:last-child th:first-child').tooltip({'placement': 'bottom', 'title': getTitle, 'template': tooltip, 'html': true});
                });

            });
        },

        tornadoInit: function(){
            
            var tornadoData = $('#tornado-data').text();
            var jsonData = JSON.parse(tornadoData);
            $('#tornado-json').JSONView(jsonData, {collapsed: true, nl2br: true});
            $('#tornado-json').JSONView('expand', 1);
        }
    };

    initApi.tornadoInit();
    initApi.redisInit();
}

$(document).ready(init);

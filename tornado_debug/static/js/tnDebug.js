(function ($, publicApi){
    var tndbApi = {
        init: function(){
            $('#tnDebug').show();
            $('#tnDebug .panelsBody').hide();
            $('#tnDebug #tnDebugShowButton').show();
            $('#tnDebug .tnDebugClose').on('click', function(){
                $('#tnDebug .panelsBody').hide();
                $('#tnDebug #tnDebugShowButton').show();
            });
            $('#tnDebug #tnDebugShowButton').on('click', function(){
                $('#tnDebug #tnDebugShowButton').hide();
                $('#tnDebug .panelsBody').show();
            });
        },
    };
    $(document).ready(tndbApi.init);
})(tndb.jQuery, tndb);

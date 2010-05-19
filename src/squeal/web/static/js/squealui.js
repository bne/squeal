$(function() {
    $('.controls-back').button({
        text: false,
        icons: { primary: 'ui-icon-seek-start' }
    });

    $('.controls-play').button({
        text: false,
        icons: { primary: 'ui-icon-pause' }
    });

    $('.controls-next').button({
        text: false,
        icons: { primary: 'ui-icon-seek-end' }
    });

    $('#sources').accordion({
        icons: false,
        fillSpace: true,
        active: 1,
        header: 'h3'
    });

    $('#playlist').accordion({
        icons: false,
        fillSpace: true
    });

    $(".progress").progressbar({
        value: 0
    });

    $('.volume').slider({
        value: 75,
        min: 0,
        max: 100
    });

    $('#main div.panel dl dt').click(function(){
        if($(this).next().is(':visible')) {
            $(this).next().hide();
        $(this).find('span.toggle').text('[+]');
        }
        else {
            $(this).next().show();
        $(this).find('span.toggle').text('[-]');
        }
    });

    $('#main div.panel dl dt').each(function(){
        $(this).next().toggle();
        $(this).prepend('<span class="toggle">[+]</span>');
    });
    
    function _resize_main() {
        var h = (
            $(window).height() - 
            $('#header').outerHeight() - $('#header').height()
        );
        $('#sources, #playlist').height(h);
    }
    
    $(window).resize(_resize_main);

    _resize_main();

});





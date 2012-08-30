$(document).ready(function() {
    
    var menu_item = 'div#header + div.toc ul li a'
    
    $('div.section').hide();
    
    current = $(menu_item + ':first').attr('href')
    next = $(menu_item + ':first').parent().next('li').children('a:first-child').attr('href');
    $(current).parent().show()
    $(current).parent().nextUntil($(next).parent()).show();
    
    $(menu_item + ':first').toggleClass('current');
    
    var speed = 200;
    
    $(menu_item).click(function() {
        
        var target = $(this).attr('href');
        var next = $(this).parent().next('li').children('a:first-child').attr('href');
        var current = '#' + $('div.section:visible > h1:first-child').attr('id');
        var parent = $(target).parent();
        
        if(target != current) {
            
            $(menu_item + '[href="' + current + '"]').toggleClass('current');
            $(this).toggleClass('current');
            
            $('div.section:visible').slideUp(speed, function() {                
                parent.delay(100).slideDown(speed);
                parent.nextUntil($(next).parent()).delay(200).slideDown(speed);
            });
        }
        
        return false;
    });
});

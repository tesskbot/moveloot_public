﻿/*=============================================================
    Authour URL: www.designbootstrap.com
    
    http://www.designbootstrap.com/

    License: MIT

    http://opensource.org/licenses/MIT

    100% Free To use For Personal And Commercial Use.

    IN EXCHANGE JUST TELL PEOPLE ABOUT THIS WEBSITE
   
========================================================  */

$(document).ready(function () {

    /*====================================
          SUBSCRIPTION   SCRIPTS 
    ======================================*/


    // $("#postcontent").submit(function (e) {
    //     e.preventDefault();
    //     $.ajax({
    //         type: "POST",
    //         url: "subscribe.php",
    //         data: $("#postcontent").serialize(),
    //          success: function (response) {
			 //  $('[name="email"]').val('');
    //            // alert(response); // FOR ACTUAL RESPONSE
			 //   alert('Thanks for  subscribing Us');
    //         }
    //     });
    //     e.preventDefault();
    // });

    // SCROLL SCRIPTS 
    $('.scroll-me a').bind('click', function (event) { //just pass scroll-me class and start scrolling
        var $anchor = $(this);
        $('html, body').stop().animate({
            scrollTop: $($anchor.attr('href')).offset().top
        }, 1000, 'easeInOutQuad');
        event.preventDefault();
    });


    $("#date-picker-2").datepicker({ 
    onSelect: function(selected) {
    $("#date-picker-2").datepicker("option","minDate", selected)
    }
    });



});

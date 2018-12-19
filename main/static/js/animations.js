$(document).ready(function(){
  
$(window).load(function(){
  initialize_page();
});

profile_options = 'closed'

$('#profile-options').hide();
$('.snackbar').hide();

$('.form-control.floatlabel').floatlabel({
    labelEndTop:'-2px'
});

$(".datepicker").datepicker({
    dateFormat: "MM dd, yy"
});

$('.clockpicker').clockpicker({
    twelvehour: true,
    donetext: 'Done',
    autoclose: false
});

$('#user-icon-container').on('click', function () {
    var $this = jQuery(this);
    if ($this.data('activated')) return false;  // Pending, return
    $this.data('activated', true);
    setTimeout(function() {
      $this.data('activated', false)
    }, 500); // Freeze for 500ms

    if ((typeof profile_options === 'undefined') || (profile_options == 'closed')){
        var travel_width = $('#profile-options').width();
        $('#user-icon-container').animate({'margin-right':travel_width+2});
        profile_options = 'open'
        setTimeout(function() {
            $('#profile-options').fadeIn();
        }, 500); // Freeze for 500ms
    }
    else{
        $('#profile-options').fadeOut();
        profile_options = 'closed'
        setTimeout(function() {
            $('#user-icon-container').animate({'margin-right':'0'});
        }, 500); // Freeze for 500ms
    }
});

});
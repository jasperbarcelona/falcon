function login(){
  $('#login-form-loader').show();
  $('#login-btn').button('loading');
  user_email = $('#user_email').val();
  user_password = $('#user_password').val();
  $.post('/user/authenticate',{
  	user_email:user_email,
  	user_password:user_password
  },
  	function(data){
	  	if (data['status'] == 'failed'){
        $('#login-error-container').show();
	  		$('#login-error').html(data['error']);
	  		$('#login-form-loader').hide();
        $('#login-btn').button('complete');
	  	}
	   	else{
	   		$(location).attr('href', '/');
	   	}
  });
}

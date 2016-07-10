Riker.RegisterForm = React.createClass({
	getInitialState: function() {
		return {
			userId: '',
			password: '',
			passwordCheck: '',
			errorMsg: ''
		};
	},
	updateField: function(field) {
		return function(event) {
			var state = {};
			state[field] = event.target.value;
			this.setState(state);
		}.bind(this);
	},
	handleError: function(msg) {
		this.setState({errorMsg: msg});
	},
	submit: function(e) {
		e.preventDefault()
		if (this.state.password !== this.state.passwordCheck) {
			this.handleError('Passwords do not match.');
		}
		else {
			$.ajax({
				url: this.props.url,
				dataType: 'json',
				type: 'POST',
				data: {
					userId: this.state.userId,
					password: this.state.password
				},
				success: function(data) {
					localStorage.setItem('loggedInUser', data.userId);
					localStorage.setItem('sessionExpiration', Date.parse(data.expiration));
					window.location.replace('/');
				},
				error: function(xhr, status, err) {
					var responseBody = $.parseJSON(xhr.responseText);
					this.handleError(responseBody.errorMsg);
				}.bind(this)
			});
		}
	},
	render: function() {
		return (
			<div>
				<form onSubmit={this.submit}>
					<label>userid: <input type="text" onChange={this.updateField('userId')} /></label><br />
					<label>password: <input type="password" onChange={this.updateField('password')} /></label><br />
					<label>confirm password: <input type="password" onChange={this.updateField('passwordCheck')} /></label><br />
					<input type="submit" value="Register" onClick={this.submit}/><br />
				</form>
				<p>{this.state.errorMsg}</p>
			</div>
		);
	}
});


Riker.Navbar = React.createClass({
	getInitialState: function() {
		return {
			loggedIn: 'sessionExpiration' in localStorage && Date.now() < localStorage.sessionExpiration
		};
	},
	logout: function() {
		$.ajax({
			url: Riker.getApiEndpoint('end-session'),
			method: 'POST'
		});
		if ('sessionExpiration' in localStorage) {
			delete localStorage.sessionExpiration;
		}
		if ('loggedInUser' in localStorage) {
			delete localStorage.loggedInUser;
		}
		this.setState({loggedIn: false});
		console.log('logged out');
	},
	render: function() {
		console.log('rendering navbar');
		var hideStyle = {
			display: 'none'
		};
		var userId = localStorage.loggedInUser || '';
		return (
			<ul>
				<li><a href="/">home</a></li>

				{/* Elements shown when logged in */}
				<li style={this.state.loggedIn ? {} : hideStyle}><a href={"/user/" + userId}>{userId}</a></li>
				<li style={this.state.loggedIn ? {cursor: 'pointer'} : hideStyle} onClick={this.logout}>logout</li>

				{/* Elements shown when logged out */}
				<li style={this.state.loggedIn ? hideStyle : {}}><a href="/login">login</a></li>
				<li style={this.state.loggedIn ? hideStyle : {}}><a href="/register">register</a></li>
			</ul>
		);
	}
});

console.log(Riker.Navbar);


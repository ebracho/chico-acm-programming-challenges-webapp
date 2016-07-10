Riker.ProblemForm = React.createClass({
	getInitialState: function() {
		return {
			title: '',
			prompt: '',
			testInput: '',
			testOutput: '',
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
		e.preventDefault();
		$.ajax({
			url: Riker.getApiEndpoint('problems'),
			dateType: 'json',
			type: 'POST',
			data: {
				title: this.state.title,
				prompt: this.state.prompt,
				testInput: this.state.testInput,
				testOutput: this.state.testOutput
			},
			success: function(data) {
				window.location.replace('/'); /* change to problem page in future */
			},
			error: function(xhr, status, err) {
				var responseBody = $.parseJSON(xhr.responseText);
				this.handleError(responseBody.errorMsg);
			}.bind(this)
		});
	},
	render: function() {
		return (
			<div>
				<form>
					<strong>Title</strong><br/>
					<input onChange={this.updateField('title')} /><br/>
					<strong>Prompt</strong><br/>
					<textarea rows="10" cols="50" onChange={this.updateField('prompt')} /><br/>
					<strong>Test Input</strong><br/>
					<textarea rows="10" cols="50" onChange={this.updateField('testInput')} /><br/>
					<strong>Test Output</strong><br/>
					<textarea rows="10" cols="50" onChange={this.updateField('testOutput')} /><br/>
					<input type="submit" value="Create Problem" onClick={this.submit}/><br/>
				</form>
				<p>{this.state.errorMsg}</p>
			</div>
		);
	}
})


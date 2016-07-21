Riker.ProblemForm = React.createClass({
	getInitialState: function() {
		return {
			title: '',
			prompt: '',
			testInput: '',
			testOutput: '',
			errorMsg: '',
			timeout: 1
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
				testOutput: this.state.testOutput,
				timeout: this.state.timeout
			},
			success: function(data) {
				window.location.replace('/problems/' + data.problemId);
			},
			error: function(xhr, status, err) {
				var responseBody = $.parseJSON(xhr.responseText);
				this.handleError(responseBody.errorMsg);
			}.bind(this)
		});
	},
	render: function() {
		var selectTimeoutNodes = [];
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
					<strong>Timeout (seconds)</strong><br/>
					<select onChange={this.updateField('timeout')}>
						<option value="1" key="1">1</option>
						<option value="2" key="2">2</option>
						<option value="3" key="3">3</option>
						<option value="4" key="4">4</option>
						<option value="5" key="5">5</option>
						<option value="6" key="6">6</option>
						<option value="7" key="7">7</option>
						<option value="8" key="8">8</option>
						<option value="9" key="9">9</option>
						<option value="10" key="10">10</option>
					</select><br/>
					<input type="submit" value="Create Problem" onClick={this.submit}/><br/>
				</form>
				<p>{this.state.errorMsg}</p>
			</div>
		);
	}
})


Riker.SolutionForm = React.createClass({
	getInitialState: function() {
		return {
			language: 'python',
			source: '',
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
			url: Riker.getApiEndpoint('problems/' + this.props.problemId + '/solutions'),
			dateType: 'json',
			type: 'POST',
			data: {
				problemId: this.props.problemId,
				language: this.state.language,
				source: this.state.source
			},
			success: function(data) {
				window.location.replace('/problems/' + this.props.problemId + '/solutions/' + data.solutionId); 
			}.bind(this),
			error: function(xhr, status, err) {
				var responseBody = $.parseJSON(xhr.responseText);
				this.handleError(responseBody.errorMsg);
			}.bind(this)
		});
	},
	getProblemPrompt: function() {
		$.ajax({
			url: Riker.getApiEndpoint('problems/' + this.props.problemId),
			dataType: 'json',
			type: 'GET',
			success: function(data) {
				this.setState({prompt: data.prompt});
			}.bind(this),
			error: function(xhr, status, err) {
				var responseBody = $.parseJSON(xhr.responseText);
				this.handleError(responseBody.errorMsg);
			}.bind(this)
		});
	},
	componentDidMount: function() {
		this.getProblemPrompt();
	},
	render: function() {
		var selectLanguageNodes = this.props.supportedLanguages.map(function(language) {
			return <option value={language} key={language}>{language}</option>
		});

		return (
			<div>
				<h3>Prompt</h3>
				<p>{this.state.prompt}</p>
				<form>
					<textarea rows="10" cols="50" onChange={this.updateField('source')} /><br/>
					<label>language</label>
					<select onChange={this.updateField('language')}>
						{selectLanguageNodes}
					</select><br/>
					<input type="submit" value="Submit Solution" onClick={this.submit}/><br/>
				</form>
				<p>{this.state.errorMsg}</p>
			</div>
		);
	}
})


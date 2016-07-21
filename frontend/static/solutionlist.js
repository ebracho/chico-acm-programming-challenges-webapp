Riker.SolutionList= React.createClass({
	getInitialState: function() {
		return {
			solutions: []
		};
	},
	loadSolutions: function() {
		$.ajax({
			url: Riker.getApiEndpoint('problems/' + this.props.problemId + '/solutions'),
			dataType: 'json',
			type: 'GET',
			success: function(data) {
				this.setState({
					solutions: data
				});
			}.bind(this),
			error: function(xhr, status, err) {
				console.log(xhr.responseText);
			}
		});
	},
	componentDidMount: function() {
		this.loadSolutions();
		setInterval(this.loadSolutions, this.props.pollInterval);
	},
	render: function() {
		var solutionNodes = this.state.solutions.map(function(solution) {
			var url = "/problems/" + this.props.problemId + '/solutions/' + solution.solutionId;
			var title = solution.userId + ' (' + solution.submissionTime + ')';
			return (
				<li key={solution.solutionId}><a href={url}>{title}</a></li>
			);
		}.bind(this));
		return (
			<ul>
				{solutionNodes}
			</ul>
		);
	}
});


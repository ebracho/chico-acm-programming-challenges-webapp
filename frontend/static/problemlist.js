Riker.ProblemList = React.createClass({
	getInitialState: function() {
		return {
			problems: []
		};
	},
	loadProblems: function() {
		$.ajax({
			url: Riker.getApiEndpoint('problems'),
			dataType: 'json',
			type: 'GET',
			success: function(data) {
				this.setState({problems: data});
			}.bind(this),
			error: function(xhr, status, err) {
				console.log(xhr.responseText);
			}
		});
	},
	componentDidMount: function() {
		this.loadProblems();
		setInterval(this.loadProblems, this.props.pollInterval);
	},
	render: function() {
		var problemNodes = this.state.problems.map(function(problem) {
			return (
				<li><a href={"/problem/" + problem.id}>{problem.title}</a></li>
			);
		});
		return (
			<ul>
				{problemNodes}
			</ul>
		);
	}
});


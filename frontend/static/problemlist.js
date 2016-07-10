Riker.ProblemList = React.createClass({
	getInitialState: function() {
		return {
			problems: []
		};
	},
	getProblems: function() {
		$.ajax({
			url: Riker.getApiEndpoint('problems'),
			dataType: 'json',
			type: 'GET',
			success: function(data) {
				this.state.problems = data;
			}.bind(this),
			error: function(xhr, status, err) {
				console.log(xhr.responseText);
			}
		});
	},
	render: function() {
		this.getProblems();
		var problemNodes = this.state.problems.map(function(problem) {
			return (
				<li><a href={"/problem/" + problem.id}>{problem.title}</a></li>
			)
		});
		return (
			<ul>
				{problemNodes}
			</ul>
		)
	}
});


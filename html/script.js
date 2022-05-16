$( document ).ready(function() {

    function formatCertainty(c){
      return ((Math.round(c * 100) / 100) * 100) + '%';
    }

    function getAnwer(result){
      if(result['_additional']['answer']['result']){
        return result['_additional']['answer'];
      }
      return null;
    }

    function processResults(results, duration){
      if(results.length > 0){
        var answer = getAnwer(results[0]);
        if(answer){
          $('#answer').html('<b>Q&amp;A answer</b>: <i style="text-transform: capitalize;">' + answer['result'] + '</i><br>');
          $('#answer').append('<b>Q&amp;A precision</b>: ' + formatCertainty(answer['certainty']) + '<br>');
          $('#answer').append('<b>Request duration</b>: ' + duration + ' sec<br>');
          $('#answer').show();
        } else {
          $('#answer').html('');
          $('#answer').hide();
        }
        console.log(answer);
      } else {
        alert('kak geen results');
      }
    }

    function requestResults(graphQL, cb){
      var start = new Date().getTime();
        $.ajax('http://semantic-search-wikipedia-with-weaviate.api.vectors.network:8080/v1/graphql', {
          data : JSON.stringify({ 'query': graphQL }),
          contentType : 'application/json',
          type : 'POST',
          success: function(result, status){
            var duration = (new Date().getTime() - start) / 1000;
            cb(result, status, duration);
          }
        })
    }

    function getQuotes(i){
        var returnArray = [];
        var quotedText = i.match(/"((?:\\.|[^"\\])*)"/g);
        if(quotedText) {
            quotedText.forEach(function(val){
                returnArray.push(val);
            });
        }
        return returnArray;
    }

    function getWhereFilter(qArray, isAppendix){
        if(qArray.length > 0 && qArray.length == 1){
            if(isAppendix === true){
              return `{
                operator: Equal
                path: ["content"]
                valueText: "` + qArray[0] + `"
              }`
            }
            return `where: {
              operator: Equal
              path: ["inArticle", "Article", "title"]
              valueString: "` + qArray[0].replaceAll('"', '') + `"
            }`
        } else if(qArray.length > 1) {
            var operandsStr = '';
            qArray.forEach(function(q){
                operandsStr += getWhereFilter([q.replaceAll('"', '')], true) + ', ';
            })
            return `where: {
              operator: And
              operands: [` + operandsStr.substring(0, operandsStr.length - 2) + `]
            }`
        }
        return ''
    }

    function formatGraphQLQuery(q, qArray){
        var gql = `{
  Get {
    Paragraph(
      ask: {
        question: "` + q + `"
        properties: ["content"]
        certainty: 0.85
      }
      ` + getWhereFilter(qArray, false) + `
      limit: 10
    ) {
      content
      order
      title
      inArticle {
        ... on Article {
          title
        }
      }
      _additional {
        certainty
        answer {
          result
          certainty
        }
      }
    }
  }
}`;

        return gql;
    }

    $('#q').keyup(function(e){
        if(e.which == 13) {
            var rawSearchString = $(this).val();
            var quotedSearchArray = getQuotes(rawSearchString);
            var searchString = rawSearchString.replaceAll('"', '');
            var graphQlQuery = formatGraphQLQuery(searchString, quotedSearchArray);
            // Execute search
            requestResults(graphQlQuery, function(result, status, duration){
                processResults(result['data']['Get']['Paragraph'], duration);
            });
            // set code block content
            $('#graphql-block').html(graphQlQuery);
        }
    });
});

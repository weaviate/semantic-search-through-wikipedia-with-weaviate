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

function formatGraphQLQuery(q, qArray){
    var gql = `{
        Get {
          Paragraph(
            ask: {
              question: "` + q + `"
              properties: ["content"]
            }
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
              answer {
                result
              }
            }
          }
        }
      }`;

    console.log(gql);
}

$( document ).ready(function() {
    $('#q').keyup(function(e){
        if(e.which == 13) {
            var rawSearchString = $(this).val();
            var quotedSearchArray = getQuotes(rawSearchString);
            var searchString = rawSearchString.replaceAll('"', '');
            formatGraphQLQuery(searchString, quotedSearchArray);
        }
    });
});

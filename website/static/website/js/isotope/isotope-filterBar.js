/*
 * Filter bar that is compatible with isotope
 * Handles clicks, calls sorting and filtering functions if applicable
 * Generates filters on top of the ones specified in HTML using sort-filter data container
 */

var filterKeywords = [];
var filterNames = [];
function isotopeFilterBarInit(){
    // start the sidebar container
    $(sideBarContainer).fixedSideBar();

    $(sideBarContainer + ' li a').each(function(){
        // set the name attribute to the text of the element if the name attribute doesn't exist.
        var attr = $(this).attr("name");
        if(typeof attr === typeof undefined || attr === false) {
            $(this).attr("name", $(this).text());
        }

        // set the style so that we get the cursor
        $(this).attr("style", 'cursor: pointer;');

        //  put this into filterKeywords
        filterKeywords.push($(this).attr("name"));
    });

    //  handle clicks on the sidebar
    $(sideBarContainer).on('click', function (e) {
        handleFilterBarClick(e)
    });


    //  go through each item in the grid
    $(gridName + ' .item').each(function(){
        // get the types of headers from categories, split by ')'
        var text = $(this).find(sortFilterDataContainer)[0].textContent;
        var textSplit = text.split(')');
        // go through textSplit, only create headers that are unique and not empty
        for(var i = 0; i < textSplit.length; i++) {
            if(textSplit[i] === "") {
                continue;
            }
            if(filterNames.indexOf(textSplit[i]) === -1) {
                filterNames.push(textSplit[i]);
            }
        }
    });
    console.log(filterNames);
    console.log(filterKeywords);
}

// handles the onclick for filter bar
function handleFilterBarClick(e)
{
    // get our text
    var text = $(e.target).attr("name");

    //formula to calculate a smooth scroll time, caps at one second.
    var timeToScroll = 1000 * (-100/(Math.abs(window.scrollY - scrollTop + 100)) + 1);
    console.log(scrollTop, timeToScroll);
    // scroll up to "scrollTop"
    $("html, body").animate({scrollTop:scrollTop}, timeToScroll);

    //handle the filtering click if it exists
    if(typeof handleFilteringClick !== typeof undefined){
        //wait for the scroll before filtering
        setTimeout(function(){handleFilteringClick(e)}, timeToScroll);
    }

    //handle the sorting click if it exists
    if(typeof handleSortingClick !== typeof undefined) {
        //wait for the scroll before sorting
        setTimeout(function(){handleSortingClick(e)}, timeToScroll);

        //only delete/insert filter keywords if sorting is enabled and a resort was triggered.
        if(filterKeywords.indexOf(text) > -1) {
            var filter_keywords_to_remove = $(filteringKeywordContainer).find('.added-filter-keywords');
            for(var i = 0; i < filter_keywords_to_remove.length; i++) {
                filter_keywords_to_remove[i].remove();
            }

            var filterMatches = [];
            for(var i = 0; i < filterNames.length; i++) {
                if(filterNames[i].indexOf(text) !== -1) {
                    filterMatches.push(filterNames[i]);
                    console.log(filterNames[i]);
                }
            }
            //sort these names so that we can put them in order
            filterMatches = sortFilterNamesByProperty(filterMatches, text);
            console.log("in filter-bar: ")
            //if there are more than 0 filter matches, add the text as a header.
            if(filterMatches.length > 0) {
                $(filteringKeywordContainer).append("<h1 class='added-filter-keywords'>" + text + "</h1>");
            }

            //put all of the properties we can filter by
            for(var i = 0; i < filterMatches.length; i++) {
                     $(filteringKeywordContainer).append("<li class='added-filter-keywords' style='list-style-type:none;cursor:pointer;'><a name='"+ filterMatches[i] +"'>" + parsePropertyValue(filterMatches[i]) + "</a></li>")
            }

            //add 'all' to the bottom if there are more than 0 filter matches
            if(filterMatches.length > 0) {
                $(filteringKeywordContainer).append("<li class='added-filter-keywords' style='list-style-type:none;cursor:pointer;'><a name='" + text + "'>all</a></li>");
            }
        }
    }





}
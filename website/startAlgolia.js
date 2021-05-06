const searchClient = algoliasearch("WDX3IWJU87", "6d5d52ff7a10d5badc85f51f4cb6a9fa");
const index = searchClient.initIndex("main");

const search = instantsearch({
    indexName: "main",
    searchClient
})

search.addWidgets([
    instantsearch.widgets.searchBox({
        container: '#searchbox',
		placeholder: '#MeToo',
		showSubmit: false,
    }),

    instantsearch.widgets.hits({
        container: '#hits',
        templates: {
			empty(results){
				return 	`Whoops! Can't find anything for <q>{{ query }}</q> :(`
			},
            item(hit) {
                console.log(hit.title);
                console.log(hit.byline);

                const snippets = hit._snippetResult.plain_text.filter((el1) => {
                    return el1.matchLevel === "full";
                })
                if (snippets === []) return null;
                return `<div class="heading light">`+hit.title+`</div>`
            }
        },
		cssClasses: {
			item: "list-item",
		},
    })
]);
search.start();
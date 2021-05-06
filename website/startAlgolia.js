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
            item(hit) {
                console.log(hit);

                const snippets = hit._snippetResult.plain_text.filter((el1) => {
                    return el1.matchLevel === "full";
                })
                if (snippets === []) return null;
                return `<h3>${JSON.stringify(snippets)}</h3>`
            }
        }
    })
]);
search.start();
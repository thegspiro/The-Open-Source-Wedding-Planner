(function () {
    'use strict';

    function tabsFor(tablist) {
        return Array.from(tablist.querySelectorAll(':scope > .tab-btn[role="tab"]'));
    }

    function selectTab(tab, moveFocus) {
        var tablist = tab.closest('.tabs[role="tablist"]');
        if (!tablist) return;

        tabsFor(tablist).forEach(function (candidate) {
            var selected = candidate === tab;
            var panel = document.getElementById(candidate.getAttribute('aria-controls'));

            candidate.classList.toggle('active', selected);
            candidate.setAttribute('aria-selected', String(selected));
            candidate.tabIndex = selected ? 0 : -1;

            if (panel) {
                panel.classList.toggle('active', selected);
                panel.hidden = !selected;
            }
        });

        if (moveFocus) tab.focus();
    }

    function handleKeydown(event) {
        var tabs = tabsFor(event.currentTarget);
        var currentIndex = tabs.indexOf(event.target);
        if (currentIndex === -1) return;

        var nextIndex;
        switch (event.key) {
            case 'ArrowLeft':
                nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
                break;
            case 'ArrowRight':
                nextIndex = (currentIndex + 1) % tabs.length;
                break;
            case 'Home':
                nextIndex = 0;
                break;
            case 'End':
                nextIndex = tabs.length - 1;
                break;
            default:
                return;
        }

        event.preventDefault();
        selectTab(tabs[nextIndex], true);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.tabs[role="tablist"]').forEach(function (tablist) {
            var tabs = tabsFor(tablist);
            tabs.forEach(function (tab) {
                tab.addEventListener('click', function () { selectTab(tab, false); });
            });
            tablist.addEventListener('keydown', handleKeydown);

            var selected = tabs.find(function (tab) {
                return tab.getAttribute('aria-selected') === 'true';
            }) || tabs[0];
            if (selected) selectTab(selected, false);
        });
    });
})();

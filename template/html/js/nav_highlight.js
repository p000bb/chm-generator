// 主项目导航标签高亮功能
(function ($) {
    'use strict';

    // 导航标签高亮功能
    function initNavigationHighlight() {
        // 获取当前页面的文件名（不包含路径和扩展名）
        const currentPage = window.location.pathname.split('/').pop().replace('.html', '');

        // 查找导航标签列表
        const $navTabs = $('.tablist li');

        if ($navTabs.length === 0) return;

        // 移除所有现有的current类
        $navTabs.removeClass('current');

        // 根据当前页面高亮对应的导航标签
        $navTabs.each(function () {
            const $tab = $(this);
            const $link = $tab.find('a');
            const href = $link.attr('href');

            if (href) {
                const tabPage = href.replace('.html', '');

                // 如果当前页面匹配导航标签的链接，则高亮
                if (tabPage === currentPage) {
                    $tab.addClass('current');
                    return false; // 找到匹配项后退出循环
                }

                // 特殊处理首页（index.html）
                if (currentPage === 'index' && tabPage === 'index') {
                    $tab.addClass('current');
                    return false;
                }

                // 如果当前页面不是index，但导航标签是首页，检查是否应该高亮
                if (tabPage === 'index' && currentPage !== 'index') {
                    // 检查当前页面是否属于首页内容
                    const isMainPage = $('body').hasClass('PageDoc') &&
                        $('.contents').length > 0 &&
                        !$('.contents').find('h1').length;

                    if (isMainPage) {
                        $tab.addClass('current');
                        return false;
                    }
                }
            }
        });

        // 如果没有找到匹配的标签，默认高亮首页
        if ($navTabs.filter('.current').length === 0) {
            $navTabs.filter(':first').addClass('current');
        }
    }

    // 确保在DOM加载完成后执行
    $(document).ready(function () {
        initNavigationHighlight();
    });

    // 页面加载完成后再次执行导航高亮（确保所有元素都已加载）
    $(window).on('load', function () {
        initNavigationHighlight();
    });

})(jQuery);

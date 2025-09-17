// 动态布局控制脚本
(function ($) {
    'use strict';

    // 等待DOM加载完成
    function initLayout() {
        // 获取页面元素
        const $topElement = $('#top');
        const $navPathElement = $('#nav-path');
        const $docContentElement = $('#doc-content');
        const $sideNavElement = $('#side-nav');
        const $navTreeElement = $('#nav-tree');

        if ($docContentElement.length === 0) return;

        // 计算可用高度
        function updateLayout() {
            const windowHeight = $(window).height();
            const topHeight = $topElement.length ? $topElement.outerHeight() : 0;
            const navPathHeight = $navPathElement.length ? $navPathElement.outerHeight() : 0;

            // 计算导航标签页的高度
            let navTabsHeight = 0;

            // 查找所有navrow元素
            const $navElements = $('[id^="navrow"]');
            $navElements.each(function () {
                navTabsHeight += $(this).outerHeight();
            });

            // 计算doc-content的可用高度
            let availableHeight = windowHeight - topHeight - navPathHeight - navTabsHeight;
            // 确保最小高度
            if (availableHeight < 200) {
                availableHeight = 200;
            }

            // 设置doc-content的高度
            $docContentElement.css({
                height: availableHeight + 'px',
                overflow: 'auto',
            });

            $navTreeElement.css('height', availableHeight + 'px');
            $sideNavElement.css('top', '');
            // 如果有侧边导航，调整其高度
            if ($sideNavElement.length) {
                $sideNavElement.css({
                    height: availableHeight + 'px',
                    overflow: 'auto',
                });
            }
        }

        // 初始设置
        updateLayout();

        // 监听窗口大小变化
        $(window).on('resize', updateLayout);

        // 监听内容变化（如果有动态内容加载）
        if (window.MutationObserver) {
            const observer = new MutationObserver(updateLayout);
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    // 确保在DOM加载完成后执行
    $(document).ready(function () {
        // 初始化布局
        initLayout();
    });
})(jQuery); 